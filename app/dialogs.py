from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QTextEdit,
    QCheckBox,
    QPushButton,
    QHBoxLayout,
)
from PyQt5.QtCore import Qt
from datetime import datetime
from .tasks_model import Task
from .translations import tr  # используем перевод


class EditTaskDialog(QDialog):
    def __init__(self, parent=None, task=None):
        super().__init__(parent)
        self.setWindowTitle(tr.get("Edit Task"))
        self.setMinimumWidth(400)

        # Локальный импорт для избегания цикла
        from .settings_widget import apply_font_to_dialog

        apply_font_to_dialog(self)

        self.task = task or Task(id=None, title="")  # создаем пустую задачу с id=None

        layout = QVBoxLayout(self)

        # Заголовок
        layout.addWidget(QLabel(tr.get("Title:")))
        self.title_edit = QLineEdit(self.task.title)
        layout.addWidget(self.title_edit)

        # Описание
        layout.addWidget(QLabel(tr.get("Description:")))
        self.desc_edit = QTextEdit(getattr(self.task, "description", ""))
        layout.addWidget(self.desc_edit)

        # Дедлайн
        layout.addWidget(QLabel(tr.get("Deadline:")))
        from PyQt5.QtWidgets import QDateEdit
        from PyQt5.QtCore import QDate

        self.deadline_edit = QDateEdit()
        self.deadline_edit.setCalendarPopup(True)
        if getattr(self.task, "deadline", None):
            self.deadline_edit.setDate(self.task.deadline)
        else:
            self.deadline_edit.setDate(QDate.currentDate())
        layout.addWidget(self.deadline_edit)

        # Pomodoro
        self.use_pomodoro_cb = QCheckBox(tr.get("Use Pomodoro"))
        self.use_pomodoro_cb.setChecked(getattr(self.task, "use_pomodoro", False))
        self.use_pomodoro_cb.toggled.connect(self.toggle_pomodoro_fields)
        layout.addWidget(self.use_pomodoro_cb)

        # Поля Pomodoro
        self.pomodoro_container = QVBoxLayout()
        layout.addLayout(self.pomodoro_container)
        self.pomodoro_work_edit = QLineEdit(
            str(getattr(self.task, "pomodoro_work", 25))
        )
        self.pomodoro_break_edit = QLineEdit(
            str(getattr(self.task, "pomodoro_break", 5))
        )
        self.pomodoro_container.addWidget(QLabel(tr.get("Work minutes:")))
        self.pomodoro_container.addWidget(self.pomodoro_work_edit)
        self.pomodoro_container.addWidget(QLabel(tr.get("Break minutes:")))
        self.pomodoro_container.addWidget(self.pomodoro_break_edit)

        self.toggle_pomodoro_fields(self.use_pomodoro_cb.isChecked())

        # Кнопки
        btn_layout = QHBoxLayout()
        self.btn_ok = QPushButton(tr.get("OK"))
        self.btn_cancel = QPushButton(tr.get("Cancel"))
        btn_layout.addWidget(self.btn_ok)
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)

        self.btn_ok.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)

    def toggle_pomodoro_fields(self, enabled):
        for i in range(self.pomodoro_container.count()):
            widget = self.pomodoro_container.itemAt(i).widget()
            if widget:
                widget.setVisible(enabled)
