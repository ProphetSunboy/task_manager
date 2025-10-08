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
from PyQt5.QtGui import QColor, QBrush
from .models import Task, Session
from .storage import load_tasks, save_tasks
from .dialogs import EditTaskDialog
from datetime import datetime, timedelta
import uuid


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


class TasksWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.tasks = load_tasks()
        self.active_task_id = None
        self._running_since = None

        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self._tick)

        main_layout = QHBoxLayout(self)

        # Список задач
        left_layout = QVBoxLayout()
        self.list_widget = QListWidget()
        self.refresh_list()
        btn_row = QHBoxLayout()
        self.btn_add = QPushButton("Добавить")
        self.btn_edit = QPushButton("Редактировать")
        self.btn_del = QPushButton("Удалить")
        btn_row.addWidget(self.btn_add)
        btn_row.addWidget(self.btn_edit)
        btn_row.addWidget(self.btn_del)
        left_layout.addWidget(self.list_widget)
        left_layout.addLayout(btn_row)

        # Правая часть
        right_layout = QVBoxLayout()
        self.label_timer = QLabel("00:00:00")
        self.label_timer.setAlignment(Qt.AlignCenter)
        self.label_timer.setStyleSheet("font-size:28px; font-weight:bold;")
        self.btn_start_stop = QPushButton("Старт")
        self.label_info = QLabel("Выберите задачу и нажмите Старт")
        self.label_spent = QLabel("Общее: 00:00:00")
        self.history_list = QListWidget()
        self.history_list.setMinimumHeight(100)
        right_layout.addWidget(self.label_timer)
        right_layout.addWidget(self.btn_start_stop)
        right_layout.addWidget(self.label_info)
        right_layout.addWidget(self.label_spent)
        right_layout.addWidget(QLabel("История:"))
        right_layout.addWidget(self.history_list)
        right_layout.addStretch()

        main_layout.addLayout(left_layout, 2)
        main_layout.addLayout(right_layout, 1)

        # Connections
        self.btn_add.clicked.connect(self.add_task)
        self.btn_edit.clicked.connect(self.edit_task)
        self.btn_del.clicked.connect(self.delete_task)
        self.list_widget.itemSelectionChanged.connect(self.show_task_info)
        self.btn_start_stop.clicked.connect(self.toggle_timer)

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
        ok = QMessageBox.question(self, "Удалить", f"Удалить задачу '{task.title}'?")
        if ok == QMessageBox.StandardButton.Yes:
            del self.tasks[idx]
            save_tasks(self.tasks)
            self.refresh_list()

    def toggle_timer(self):
        item = self.list_widget.currentItem()
        if not item:
            QMessageBox.information(self, "Инфо", "Выберите задачу.")
            return
        idx = self.list_widget.currentRow()
        task = self.tasks[idx]

        if self.active_task_id is None:
            self.active_task_id = task.id
            self._running_since = datetime.now()
            task.sessions.append(Session(start=self._running_since))
            self.btn_start_stop.setText("Стоп")
            self.label_info.setText(f"Трекинг: {task.title}")
            self.timer.start()
        else:
            self.timer.stop()
            task = next((t for t in self.tasks if t.id == self.active_task_id), None)
            if task:
                for s in reversed(task.sessions):
                    if s.end is None:
                        s.end = datetime.now()
                        break
                self._recalc_task_time(task)
            save_tasks(self.tasks)
            self.active_task_id = None
            self._running_since = None
            self.btn_start_stop.setText("Старт")
            self.label_info.setText("Трекинг остановлен")
            self.refresh_list()
            self.show_task_info()

    def _tick(self):
        if not self.active_task_id or not self._running_since:
            return
        task = next((t for t in self.tasks if t.id == self.active_task_id), None)
        if not task:
            return
        elapsed = (datetime.now() - self._running_since).total_seconds()
        self.label_timer.setText(format_seconds(task.time_spent + elapsed))

    def _recalc_task_time(self, task: Task):
        total_seconds = sum(
            (s.end - s.start).total_seconds() for s in task.sessions if s.end
        )
        task.time_spent = total_seconds

    def update_time_info(self, task: Task):
        times = compute_task_time(task)
        elapsed = 0
        if self.active_task_id == task.id and self._running_since:
            elapsed = (datetime.now() - self._running_since).total_seconds()

        total_time = times["total"] + elapsed
        today_time = times["today"] + elapsed
        week_time = times["week"] + elapsed
        month_time = times["month"] + elapsed

        self.label_spent.setText(f"Общее: {format_seconds(total_time)}")
        self.label_info.setText(
            f"Сегодня: {format_seconds(today_time)} | Неделя: {format_seconds(week_time)} | Месяц: {format_seconds(month_time)}"
        )

    def show_task_info(self):
        item = self.list_widget.currentItem()
        if not item:
            self.history_list.clear()
            self.label_spent.setText("Общее: 00:00:00")
            self.label_info.setText("")
            return
        idx = self.list_widget.currentRow()
        task = self.tasks[idx]
        self.update_time_info(task)

        # История
        self.history_list.clear()
        now = datetime.now()
        for s in task.sessions:
            start = s.start.strftime("%Y-%m-%d %H:%M:%S")
            end = s.end.strftime("%Y-%m-%d %H:%M:%S") if s.end else "идёт..."
            entry = f"{start} — {end}"
            item_widget = QListWidgetItem(entry)
            if s.end is None:
                item_widget.setBackground(QBrush(QColor("#2ecc71")))
            self.history_list.addItem(item_widget)
