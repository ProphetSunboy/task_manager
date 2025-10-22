# app/tasks_widget.py
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QListWidget,
    QPushButton,
    QLabel,
    QListWidgetItem,
    QMessageBox,
    QTextEdit,
)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QBrush, QColor
from .models import Task, Session
from .storage import load_tasks, save_tasks
from .dialogs import EditTaskDialog
from datetime import datetime, timedelta
import uuid
import winsound
from .translations import tr
from .ai_assistant import get_task_advice, get_all_tasks_advice


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
        self.short_break = int(task.pomodoro_break) * 60
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
    def __init__(self, settings=None):
        super().__init__()
        self.settings = settings or {}
        self.tasks = load_tasks()
        self.active_task_id = None
        self._running_since = None

        # Pomodoro state
        self.pomodoro_mgr = None
        self.pomodoro_remaining = 0
        self.pomodoro_phase = None  # "Work" / "Break" / "Long break"
        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self._tick)

        self._build_ui()
        # apply font if settings supplied via SettingsWidget (main applies too)
        self.apply_font_size()
        self.retranslateUi()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        top_layout = QHBoxLayout()
        # Список задач
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

        # Правая часть
        right_layout = QVBoxLayout()
        self.label_timer = QLabel("00:00:00")
        self.label_timer.setAlignment(Qt.AlignCenter)
        self.label_timer.setStyleSheet("font-size:28px; font-weight:bold;")
        self.btn_start_stop = QPushButton()
        self.label_info = QLabel()
        self.label_spent = QLabel()
        self.label_pomodoro_count = QLabel()
        self.history_label = QLabel(tr("History:"))
        self.history_list = QListWidget()
        self.history_list.setMinimumHeight(100)
        right_layout.addWidget(self.label_timer)
        right_layout.addWidget(self.btn_start_stop)
        right_layout.addWidget(self.label_info)
        right_layout.addWidget(self.label_spent)
        right_layout.addWidget(self.label_pomodoro_count)
        right_layout.addWidget(self.history_label)
        right_layout.addWidget(self.history_list)
        right_layout.addStretch()

        top_layout.addLayout(left_layout, 2)
        top_layout.addLayout(right_layout, 1)

        main_layout.addLayout(top_layout)

        # ИИ-ассистент
        self.ai_label = QTextEdit()
        self.ai_label.setReadOnly(True)
        self.ai_label.setMinimumHeight(100)  # высота блока
        self.ai_label.setStyleSheet("background-color: #f0f0f0; padding: 5px;")
        main_layout.addWidget(self.ai_label)

        self.btn_generate_all = QPushButton(tr("Generate for all tasks"))
        main_layout.addWidget(self.btn_generate_all)

        # Сигналы
        self.list_widget.itemSelectionChanged.connect(self.update_ai_for_selected)
        self.btn_generate_all.clicked.connect(self.generate_ai_for_all)

        # Connections
        self.btn_add.clicked.connect(self.add_task)
        self.btn_edit.clicked.connect(self.edit_task)
        self.btn_del.clicked.connect(self.delete_task)
        self.list_widget.itemSelectionChanged.connect(self.show_task_info)
        self.btn_start_stop.clicked.connect(self.toggle_timer)

    def retranslateUi(self):
        # переводы всех статичных элементов
        self.btn_add.setText(tr("Add"))
        self.btn_edit.setText(tr("Edit"))
        self.btn_del.setText(tr("Delete"))
        # кнопка старт/стоп обновляется в зависимости от состояния
        self.btn_start_stop.setText(
            tr("Start") if not self.active_task_id else tr("Stop")
        )
        # info label отображается в зависимости от выбора задачи
        if not self.active_task_id:
            self.label_info.setText(tr("Select a task"))
        else:
            # если трекинг идёт, обновим метку (оставляем текущий формат)
            # but ensure "Tracking" word is translated
            text = self.label_info.text()
            # если в тексте встречается английское "Tracking", заменим
            if "Tracking" in text or "Трекинг" in text:
                # rebuild with translated prefix
                # try to extract task title part after colon
                parts = text.split(":", 1)
                if len(parts) == 2:
                    title_part = parts[1].strip()
                    self.label_info.setText(f"{tr('Tracking')}: {title_part}")
        self.history_label.setText(tr("History:"))
        # refresh lists and details
        self.refresh_list()
        self.show_task_info()

    def update_ai_for_selected(self):
        """Обновляет подсказки для выбранной задачи"""
        item = self.list_widget.currentItem()
        if not item:
            self.ai_label.setText("")
            return
        idx = self.list_widget.currentRow()
        task = self.tasks[idx]
        self.ai_label.setText(get_task_advice(task))

    def generate_ai_for_all(self):
        """Генерирует общие рекомендации для всех задач"""
        self.ai_label.setText(get_all_tasks_advice(self.tasks))

    def refresh_list(self):
        self.list_widget.clear()
        for t in self.tasks:
            text = t.title or "(no title)"
            if getattr(t, "is_completed", False):
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
        dlg = EditTaskDialog(task=self.tasks[idx], parent=self)
        if dlg.exec_():
            self.tasks[idx] = dlg.get_task()
            save_tasks(self.tasks)
            self.refresh_list()

    def delete_task(self):
        item = self.list_widget.currentItem()
        if not item:
            return
        idx = self.list_widget.currentRow()
        if idx < 0 or idx >= len(self.tasks):
            return
        task = self.tasks[idx]
        ok = QMessageBox.question(
            self, tr("Delete task"), f"{tr('Delete task')} '{task.title}'?"
        )
        if ok == QMessageBox.StandardButton.Yes:
            del self.tasks[idx]
            save_tasks(self.tasks)
            self.refresh_list()
            # очистим подробности
            self._stop_timer_ui()

    def toggle_timer(self):
        item = self.list_widget.currentItem()
        if not item:
            QMessageBox.information(self, tr("Info"), tr("Select a task"))
            return
        idx = self.list_widget.currentRow()
        task = self.tasks[idx]

        # Запуск
        if self.active_task_id is None:
            self.active_task_id = task.id
            # Если Pomodoro включён — запуск менеджера
            if getattr(task, "use_pomodoro", False):
                self.pomodoro_mgr = PomodoroManager(task)
                self.pomodoro_remaining, self.pomodoro_phase = (
                    self.pomodoro_mgr.get_initial()
                )
                # если фаза "Work" — создаём сессию
                if self.pomodoro_phase == tr("Work"):
                    s = Session(start=datetime.now(), end=None)
                    task.sessions.append(s)
                    self._running_since = datetime.now()
            else:
                # обычный трекинг: создаём одну сессию (идёт пока не нажмут стоп)
                s = Session(start=datetime.now(), end=None)
                task.sessions.append(s)
                self._running_since = datetime.now()

            self.btn_start_stop.setText(tr("Stop"))
            self.label_info.setText(
                f"{tr('Tracking')}: {task.title} — {self.pomodoro_phase or tr('Work')}"
            )
            self.timer.start()
        else:
            # Стоп (пауза/остановка)
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
            # Pomodoro flow
            self.pomodoro_remaining -= 1
            if self.pomodoro_remaining < 0:
                duration, phase = self.pomodoro_mgr.next_phase()
                # если переход на перерыв — закрываем рабочую сессию
                if self.pomodoro_mgr.is_break:
                    for s in reversed(task.sessions):
                        if s.end is None:
                            s.end = datetime.now()
                            break
                    save_tasks(self.tasks)
                else:
                    # переключились на Work => начинаем новую сессию
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
                f"{tr('Pomodoro')}: {self.pomodoro_mgr.current_cycle}/{self.pomodoro_mgr.cycles_before_long}"
            )
            self.update_time_info(task)
            self._populate_history(task)
        else:
            # обычный счётчик
            if self._running_since:
                elapsed = (datetime.now() - self._running_since).total_seconds()
            else:
                elapsed = 0
            self.label_timer.setText(format_seconds(int(task.time_spent + elapsed)))
            self.label_info.setText(f"{tr('Tracking')}: {task.title}")
            self.update_time_info(task)
            self._populate_history(task)

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
        self.history_list.clear()

    def show_task_info(self):
        item = self.list_widget.currentItem()
        if not item:
            self.label_spent.setText("")
            self.history_list.clear()
            return
        idx = self.list_widget.currentRow()
        if idx < 0 or idx >= len(self.tasks):
            # индекс недействителен — ничего не делаем
            self.history_label.clear()  # или обновляем интерфейс соответствующим образом
            return
        task = self.tasks[idx]
        self.update_time_info(task)
        self._populate_history(task)

    def update_time_info(self, task):
        times = compute_task_time(task)
        self.label_spent.setText(
            f"{tr('Today')}: {format_seconds(times['today'])}, {tr('Week')}: {format_seconds(times['week'])}, {tr('Total')}: {format_seconds(times['total'])}"
        )

    def _populate_history(self, task):
        self.history_list.clear()
        now = datetime.now()
        for s in task.sessions:
            start = s.start.strftime("%Y-%m-%d %H:%M:%S")
            end = (
                s.end.strftime("%Y-%m-%d %H:%M:%S")
                if s.end
                else tr("...running") if self.pomodoro_phase else "идёт..."
            )
            entry = f"{start} — {end}"
            item_widget = QListWidgetItem(entry)
            if s.end is None:
                item_widget.setBackground(QBrush(QColor("#2ecc71")))
            self.history_list.addItem(item_widget)

    def apply_font_size(self):
        # локальный запасной метод: применим размер шрифта от self.settings, если есть
        font_size = (
            int(self.settings.get("font_size", 12))
            if getattr(self, "settings", None)
            else 12
        )
        font = self.font()
        font.setPointSize(font_size)
        self.setFont(font)

    def closeEvent(self, event):
        # при закрытии, если активна задача — завершим текущую сессию и сохраним
        if self.active_task_id:
            task = next((t for t in self.tasks if t.id == self.active_task_id), None)
            if task:
                for s in reversed(task.sessions):
                    if s.end is None:
                        s.end = datetime.now()
                        break
                save_tasks(self.tasks)
        event.accept()
