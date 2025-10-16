from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QTextEdit,
    QCheckBox,
    QPushButton,
    QHBoxLayout,
    QApplication,
    QComboBox,
    QDateEdit,
)
from PyQt5.QtCore import Qt, QDate
from datetime import datetime
from .models import Task
from .translations import tr  # используем перевод


class EditTaskDialog(QDialog):
    def __init__(self, parent=None, task=None):
        super().__init__(parent)
        self.task = task or Task(id=None, title="")

        self.setWindowTitle(tr("Edit Task"))
        self.setMinimumWidth(600)

        # Применяем шрифт приложения
        app = QApplication.instance()
        if app:
            self.setFont(app.font())

        main_layout = QHBoxLayout(self)

        # ----------------- Левая колонка: заголовок, описание, комментарий -----------------
        left_layout = QVBoxLayout()
        left_layout.setSpacing(10)

        # Заголовок
        left_layout.addWidget(QLabel(tr("Title:")))
        self.title_edit = QLineEdit(self.task.title)
        left_layout.addWidget(self.title_edit)

        # Описание
        left_layout.addWidget(QLabel(tr("Description:")))
        self.desc_edit = QTextEdit(getattr(self.task, "description", ""))
        self.desc_edit.setFixedHeight(100)
        left_layout.addWidget(self.desc_edit)

        # Комментарий (если есть)
        left_layout.addWidget(QLabel(tr("Comment:")))
        self.comment_edit = QTextEdit(getattr(self.task, "comment", ""))
        self.comment_edit.setFixedHeight(60)
        left_layout.addWidget(self.comment_edit)

        main_layout.addLayout(left_layout, 2)

        # ----------------- Правая колонка: дедлайн, периодичность, Pomodoro -----------------
        right_layout = QVBoxLayout()
        right_layout.setSpacing(10)

        # Дедлайн
        self.enable_deadline_cb = QCheckBox(tr("Enable Deadline"))
        self.enable_deadline_cb.setChecked(
            getattr(self.task, "deadline", None) is not None
        )
        self.enable_deadline_cb.toggled.connect(self.toggle_deadline)
        right_layout.addWidget(self.enable_deadline_cb)

        from PyQt5.QtWidgets import QDateEdit
        from PyQt5.QtCore import QDate

        self.deadline_edit = QDateEdit()
        self.deadline_edit.setCalendarPopup(True)
        if getattr(self.task, "deadline", None):
            self.deadline_edit.setDate(self.task.deadline)
        else:
            self.deadline_edit.setDate(QDate.currentDate())
        self.deadline_edit.setEnabled(self.enable_deadline_cb.isChecked())
        right_layout.addWidget(self.deadline_edit)

        # Выделено времени
        right_layout.addWidget(QLabel(tr("Allocated time (min):")))
        self.time_alloc_edit = QLineEdit(str(getattr(self.task, "time_allocated", 0)))
        right_layout.addWidget(self.time_alloc_edit)

        # Периодичность
        right_layout.addWidget(QLabel(tr("Repeat:")))
        from PyQt5.QtWidgets import QComboBox

        self.recurrence_combo = QComboBox()
        self.recurrence_combo.addItems(
            [tr("None"), tr("Daily"), tr("Weekly"), tr("Monthly")]
        )
        self.recurrence_combo.setCurrentText(
            getattr(self.task, "recurrence", tr("None"))
        )
        right_layout.addWidget(self.recurrence_combo)

        # Pomodoro
        self.use_pomodoro_cb = QCheckBox(tr("Use Pomodoro"))
        self.use_pomodoro_cb.setChecked(getattr(self.task, "use_pomodoro", False))
        self.use_pomodoro_cb.toggled.connect(self.toggle_pomodoro_fields)
        right_layout.addWidget(self.use_pomodoro_cb)

        self.pomodoro_container = QVBoxLayout()
        self.pomodoro_work_edit = QLineEdit(
            str(getattr(self.task, "pomodoro_work", 25))
        )
        self.pomodoro_break_edit = QLineEdit(
            str(getattr(self.task, "pomodoro_break", 5))
        )
        self.pomodoro_cycles_edit = QLineEdit(
            str(getattr(self.task, "pomodoro_cycles", 4))
        )

        self.pomodoro_container.addWidget(QLabel(tr("Work minutes:")))
        self.pomodoro_container.addWidget(self.pomodoro_work_edit)
        self.pomodoro_container.addWidget(QLabel(tr("Break minutes:")))
        self.pomodoro_container.addWidget(self.pomodoro_break_edit)
        self.pomodoro_container.addWidget(QLabel(tr("Cycles before long break:")))
        self.pomodoro_container.addWidget(self.pomodoro_cycles_edit)

        right_layout.addLayout(self.pomodoro_container)
        self.toggle_pomodoro_fields(self.use_pomodoro_cb.isChecked())

        # ----------------- Кнопки OK/Cancel -----------------
        btn_layout = QHBoxLayout()
        self.btn_ok = QPushButton(tr("OK"))
        self.btn_cancel = QPushButton(tr("Cancel"))
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_ok)
        btn_layout.addWidget(self.btn_cancel)
        right_layout.addLayout(btn_layout)

        main_layout.addLayout(right_layout, 1)

        self.btn_ok.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)

    def toggle_pomodoro_fields(self, enabled):
        for i in range(self.pomodoro_container.count()):
            widget = self.pomodoro_container.itemAt(i).widget()
            if widget:
                widget.setVisible(enabled)

    def toggle_deadline(self, enabled):
        self.deadline_edit.setEnabled(enabled)

    def retranslateUi(self):
        self.setWindowTitle(tr("Edit Task"))
        self.lbl_title.setText(tr("Title:"))
        self.lbl_desc.setText(tr("Description:"))
        self.deadline_checkbox.setText(tr("Enable Deadline"))
        self.use_pomodoro_cb.setText(tr("Use Pomodoro"))
        self.pomodoro_work_lbl.setText(tr("Work minutes:"))
        self.pomodoro_break_lbl.setText(tr("Break minutes:"))
        self.freq_lbl.setText(tr("Repeat:"))
        self.btn_ok.setText(tr("OK"))
        self.btn_cancel.setText(tr("Cancel"))
        # обновляем элементы combo с периодичностью
        self.freq_combo.setItemText(0, tr("No repeat"))
        self.freq_combo.setItemText(1, tr("Daily"))
        self.freq_combo.setItemText(2, tr("Weekly"))
        self.freq_combo.setItemText(3, tr("Monthly"))

    def get_task(self):
        """Возвращает объект Task с актуальными данными из диалога"""
        from .models import Task

        self.task.title = self.title_edit.text()
        self.task.description = self.desc_edit.toPlainText()
        self.task.time_allocated = int(self.time_alloc_edit.text())

        # Дедлайн
        self.task.deadline = self.deadline_edit.date().toPyDate()

        # Pomodoro
        self.task.use_pomodoro = self.use_pomodoro_cb.isChecked()
        if self.task.use_pomodoro:
            try:
                self.task.pomodoro_work = int(self.pomodoro_work_edit.text())
                self.task.pomodoro_break = int(self.pomodoro_break_edit.text())
            except ValueError:
                self.task.pomodoro_work = 25
                self.task.pomodoro_break = 5
        else:
            self.task.pomodoro_work = 0
            self.task.pomodoro_break = 0

        # Периодичность
        self.task.periodicity = (
            self.periodicity_cb.currentText()
            if hasattr(self, "periodicity_cb")
            else None
        )

        # Дедлайн включён или нет
        self.task.deadline_enabled = (
            self.deadline_enabled_cb.isChecked()
            if hasattr(self, "deadline_enabled_cb")
            else False
        )

        return self.task
