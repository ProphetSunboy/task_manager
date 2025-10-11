# tasks_widget.py
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QListWidget,
    QPushButton,
    QLabel,
    QListWidgetItem,
    QMessageBox,
)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFont
from .models import Task, Session
from .storage import load_tasks, save_tasks
from .dialogs import EditTaskDialog
from datetime import datetime, timedelta
import uuid
import winsound
from .translations import tr


def format_seconds(seconds):
    seconds = int(seconds)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02}:{m:02}:{s:02}"


def compute_task_time(task):
    now = datetime.now()
    today_start = datetime(now.year, now.month, now.day)
    week_start = today_start - timedelta(days=today_start.weekday())
    month_start = datetime(now.year, now.month, 1)

    total = 0
    today = 0
    week = 0
    month = 0

    for s in task.sessions:
        start = s.start
        end = s.end or now
        delta = (end - start).total_seconds()
        total += delta
        if start >= today_start:
            today += delta
        if start >= week_start:
            week += delta
        if start >= month_start:
            month += delta

    return {"total": total, "today": today, "week": week, "month": month}


class PomodoroManager:
    """Управляет состоянием Pomodoro-циклов для одной задачи."""

    def __init__(self, task: Task):
        self.task = task
        self.work_duration = int(task.pomodoro_work) * 60
        self.short_break = int(task.pomodoro_short) * 60
        self.long_break = int(task.pomodoro_long) * 60
        self.cycles_before_long = int(task.pomodoro_cycles)
        self.current_cycle = 0
        self.is_break = False

    def get_initial(self):
        self.is_break = False
        self.current_cycle = 0
        return self.work_duration, tr("Work")

    def next_phase(self):
        if not self.is_break:
            self.current_cycle += 1
            self.is_break = True
            if self.current_cycle % self.cycles_before_long == 0:
                return self.long_break, tr("Long break")
            else:
                return self.short_break, tr("Break")
        else:
            self.is_break = False
            return self.work_duration, tr("Work")


class TasksWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.tasks = load_tasks()
        self.active_task_id = None
        self._running_since = None
        self.pomodoro_mgr = None
        self.pomodoro_remaining = 0
        self.pomodoro_phase = None

        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self._tick)

        self.init_ui()
        self.apply_font_size()
        self.retranslateUi()

    def init_ui(self):
        main_layout = QHBoxLayout(self)

        # Левая часть (список задач)
        left_layout = QVBoxLayout()
        self.list_widget = QListWidget()
        self.refresh_list()

        btn_row = QHBoxLayout()
        self.btn_add = QPushButton()
        self.btn_edit = QPushButton()
        self.btn_del = QPushButton()
        btn_row.addWidget(self.btn_add)
        btn_row.addWidget(self.btn_edit)
        btn_row.addWidget(self.btn_del)

        left_layout.addWidget(self.list_widget)
        left_layout.addLayout(btn_row)

        # Правая часть (таймер и детали)
        right_layout = QVBoxLayout()
        self.label_timer = QLabel("00:00:00")
        self.label_timer.setAlignment(Qt.AlignCenter)
        self.label_timer.setStyleSheet("font-weight:bold;")
        self.btn_start_stop = QPushButton()
        self.label_info = QLabel()
        self.label_spent = QLabel()
        self.label_pomodoro_count = QLabel()
        self.history_list = QListWidget()
        self.history_list.setMinimumHeight(100)

        right_layout.addWidget(self.label_timer)
        right_layout.addWidget(self.btn_start_stop)
        right_layout.addWidget(self.label_info)
        right_layout.addWidget(self.label_spent)
        right_layout.addWidget(self.label_pomodoro_count)
        right_layout.addWidget(QLabel(tr("History:")))
        right_layout.addWidget(self.history_list)
        right_layout.addStretch()

        main_layout.addLayout(left_layout, 2)
        main_layout.addLayout(right_layout, 1)

        # Сигналы кнопок
        self.btn_add.clicked.connect(self.add_task)
        self.btn_edit.clicked.connect(self.edit_task)
        self.btn_del.clicked.connect(self.delete_task)
        self.list_widget.itemSelectionChanged.connect(self.show_task_info)
        self.btn_start_stop.clicked.connect(self.toggle_timer)

    def retranslateUi(self):
        self.btn_add.setText(tr("Add"))
        self.btn_edit.setText(tr("Edit"))
        self.btn_del.setText(tr("Delete"))
        self.btn_start_stop.setText(
            tr("Start") if not self.active_task_id else tr("Stop")
        )
        self.label_info.setText(
            tr("Select a task") if not self.active_task_id else self.label_info.text()
        )
        self.refresh_list()
        self.show_task_info()

    def refresh_list(self):
        self.list_widget.clear()
        for t in self.tasks:
            text = t.title
            if t.is_completed:
                text += " (✓)"
            if t.is_overdue():
                text = "❗ " + text
            self.list_widget.addItem(text)

    def add_task(self):
        dlg = EditTaskDialog(parent=self)
        if dlg.exec_():
            t = dlg.get_task()
            t.id = str(uuid.uuid4())
            t.start_date = datetime.now()
            self.tasks.append(t)
            save_tasks(self.tasks)
            self.refresh_list()

    def edit_task(self):
        item = self.list_widget.currentItem()
        if not item:
            return
        idx = self.list_widget.currentRow()
        dlg = EditTaskDialog(self.tasks[idx], parent=self)
        if dlg.exec_():
            self.tasks[idx] = dlg.get_task()
            save_tasks(self.tasks)
            self.refresh_list()

    def delete_task(self):
        item = self.list_widget.currentItem()
        if not item:
            return
        idx = self.list_widget.currentRow()
        task = self.tasks[idx]
        ok = QMessageBox.question(
            self, tr("Delete"), f"{tr('Delete task')} '{task.title}'?"
        )
        if ok == QMessageBox.StandardButton.Yes:
            del self.tasks[idx]
            save_tasks(self.tasks)
            self.refresh_list()

    def toggle_timer(self):
        item = self.list_widget.currentItem()
        if not item:
            QMessageBox.information(self, tr("Info"), tr("Select a task"))
            return
        idx = self.list_widget.currentRow()
        task = self.tasks[idx]

        if self.active_task_id is None:
            self.active_task_id = task.id
            if getattr(task, "use_pomodoro", False):
                self.pomodoro_mgr = PomodoroManager(task)
                self.pomodoro_remaining, self.pomodoro_phase = (
                    self.pomodoro_mgr.get_initial()
                )
                s = Session(start=datetime.now(), end=None)
                task.sessions.append(s)
                self._running_since = datetime.now()
            else:
                s = Session(start=datetime.now(), end=None)
                task.sessions.append(s)
                self._running_since = datetime.now()

            self.btn_start_stop.setText(tr("Stop"))
            self.label_info.setText(
                f"{tr('Tracking')}: {task.title} — {self.pomodoro_phase}"
            )
            self.timer.start()
        else:
            current = next((t for t in self.tasks if t.id == self.active_task_id), None)
            if current:
                for s in reversed(current.sessions):
                    if s.end is None:
                        s.end = datetime.now()
                        break
                save_tasks(self.tasks)

            self._stop_timer_ui()

    def _tick(self):
        if not self.active_task_id:
            return
        task = next((t for t in self.tasks if t.id == self.active_task_id), None)
        if not task:
            return

        if getattr(task, "use_pomodoro", False) and self.pomodoro_mgr:
            self.pomodoro_remaining -= 1
            if self.pomodoro_remaining < 0:
                duration, phase = self.pomodoro_mgr.next_phase()
                if self.pomodoro_mgr.is_break:
                    for s in reversed(task.sessions):
                        if s.end is None:
                            s.end = datetime.now()
                            break
                    save_tasks(self.tasks)
                else:
                    s = Session(start=datetime.now(), end=None)
                    task.sessions.append(s)
                    self._running_since = datetime.now()

                self.pomodoro_remaining = duration
                self.pomodoro_phase = phase
                winsound.MessageBeep()

            self.label_timer.setText(format_seconds(self.pomodoro_remaining))
            self.label_info.setText(
                f"{tr('Tracking')}: {task.title} — {self.pomodoro_phase}"
            )
            self.label_pomodoro_count.setText(
                f"Pomodoro: {self.pomodoro_mgr.current_cycle}/{self.pomodoro_mgr.cycles_before_long}"
            )
            self.update_time_info(task)
        else:
            if self._running_since:
                elapsed = (datetime.now() - self._running_since).total_seconds()
            else:
                elapsed = 0
            self.label_timer.setText(format_seconds(int(task.time_spent + elapsed)))
            self.label_info.setText(f"{tr('Tracking')}: {task.title}")
            self.update_time_info(task)

    def _stop_timer_ui(self):
        self.active_task_id = None
        self._running_since = None
        self.pomodoro_mgr = None
        self.pomodoro_remaining = 0
        self.pomodoro_phase = None
        self.btn_start_stop.setText(tr("Start"))
        self.label_timer.setText("00:00:00")
        self.label_info.setText(tr("Select a task"))
        self.label_pomodoro_count.setText("")

    def show_task_info(self):
        item = self.list_widget.currentItem()
        if not item:
            return
        idx = self.list_widget.currentRow()
        task = self.tasks[idx]
        self.update_time_info(task)

    def update_time_info(self, task):
        times = compute_task_time(task)
        self.label_spent.setText(
            f"{tr('Today')}: {format_seconds(times['today'])}, {tr('Week')}: {format_seconds(times['week'])}, {tr('Total')}: {format_seconds(times['total'])}"
        )

    def apply_font_size(self):
        font_size = getattr(self, "settings", {}).get("font_size", 12)
        font = self.font()
        font.setPointSize(font_size)
        self.setFont(font)

    def closeEvent(self, event):
        if self.active_task_id:
            task = next((t for t in self.tasks if t.id == self.active_task_id), None)
            if task:
                for s in reversed(task.sessions):
                    if s.end is None:
                        s.end = datetime.now()
                        break
                save_tasks(self.tasks)
        event.accept()
