from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QTextEdit,
    QPushButton,
    QLabel,
    QCheckBox,
    QDateTimeEdit,
    QSpinBox,
    QFormLayout,
    QComboBox,
)
from PyQt5.QtCore import QDateTime
from .models import Task
from .settings_widget import apply_font_to_dialog


class EditTaskDialog(QDialog):
    def __init__(self, task: Task = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Редактирование задачи")
        self.setMinimumWidth(600)
        self.task = task

        # Основные поля
        self.title_edit = QLineEdit(task.title if task else "")
        self.desc_edit = QTextEdit(task.description if task else "")
        self.comment_edit = QTextEdit(task.comment if task else "")

        # Дедлайн
        self.use_deadline_cb = QCheckBox("Использовать дедлайн")
        self.deadline_edit = QDateTimeEdit()
        self.deadline_edit.setCalendarPopup(True)
        if task and task.deadline:
            self.use_deadline_cb.setChecked(True)
            self.deadline_edit.setDateTime(QDateTime(task.deadline))
        else:
            self.deadline_edit.setEnabled(False)
            self.deadline_edit.setDateTime(QDateTime.currentDateTime())
        self.use_deadline_cb.toggled.connect(self.deadline_edit.setEnabled)

        # Время
        self.allocated_spin = QSpinBox()
        self.allocated_spin.setRange(0, 60 * 24 * 365)
        self.allocated_spin.setValue(task.time_allocated if task else 60)

        # Периодичность
        self.periodic_cb = QCheckBox("Периодическая")
        self.period_type_combo = QComboBox()
        self.period_type_combo.addItems(["День", "Неделя", "Месяц"])
        self.period_type_combo.setEnabled(False)

        self.weekday_label = QLabel("День недели:")
        self.weekday_combo = QComboBox()
        self.weekday_combo.addItems(["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"])
        self.weekday_combo.setEnabled(False)
        self.weekday_combo.setVisible(False)
        self.weekday_label.setVisible(False)

        self.month_label = QLabel("Число месяца:")
        self.month_day_spin = QSpinBox()
        self.month_day_spin.setRange(1, 31)
        self.month_day_spin.setEnabled(False)
        self.month_day_spin.setVisible(False)
        self.month_label.setVisible(False)

        # Логика отображения периодичности
        self.periodic_cb.toggled.connect(self.period_type_combo.setEnabled)
        self.period_type_combo.currentTextChanged.connect(self.update_period_widgets)

        # Кнопки
        btn_save = QPushButton("Сохранить")
        btn_cancel = QPushButton("Отмена")
        btn_save.clicked.connect(self.accept)
        btn_cancel.clicked.connect(self.reject)

        # Layout
        main_layout = QHBoxLayout()
        left = QVBoxLayout()
        right = QFormLayout()

        left.addWidget(QLabel("Название"))
        left.addWidget(self.title_edit)
        left.addWidget(QLabel("Описание"))
        left.addWidget(self.desc_edit)
        left.addWidget(QLabel("Комментарий"))
        left.addWidget(self.comment_edit)

        right.addRow(self.use_deadline_cb, self.deadline_edit)
        right.addRow(QLabel("Выделено (мин):"), self.allocated_spin)
        right.addRow(self.periodic_cb, self.period_type_combo)
        right.addRow(self.weekday_label, self.weekday_combo)
        right.addRow(self.month_label, self.month_day_spin)
        right.addRow(btn_save, btn_cancel)

        main_layout.addLayout(left, 2)
        main_layout.addLayout(right, 1)
        self.setLayout(main_layout)

        # Если есть задача с периодичностью, загружаем её значения
        if task and task.is_periodic:
            self.periodic_cb.setChecked(True)
            if task.period_type:
                self.period_type_combo.setCurrentText(task.period_type)
            self.update_period_widgets(task.period_type)
            if task.period_type == "Неделя" and getattr(task, "period_value", None):
                self.weekday_combo.setCurrentText(task.period_value)
            elif task.period_type == "Месяц" and getattr(task, "period_value", None):
                self.month_day_spin.setValue(task.period_value or 1)

        # Применяем глобальный шрифт
        apply_font_to_dialog(self)

    def update_period_widgets(self, value):
        # Скрываем все
        self.weekday_combo.setVisible(False)
        self.weekday_combo.setEnabled(False)
        self.weekday_label.setVisible(False)

        self.month_day_spin.setVisible(False)
        self.month_day_spin.setEnabled(False)
        self.month_label.setVisible(False)

        # Показываем и активируем нужный виджет
        if value == "Неделя":
            self.weekday_combo.setVisible(True)
            self.weekday_combo.setEnabled(True)
            self.weekday_label.setVisible(True)
        elif value == "Месяц":
            self.month_day_spin.setVisible(True)
            self.month_day_spin.setEnabled(True)
            self.month_label.setVisible(True)

    def get_task(self) -> Task:
        t = self.task or Task(id="", title="")
        t.title = self.title_edit.text()
        t.description = self.desc_edit.toPlainText()
        t.comment = self.comment_edit.toPlainText()
        t.time_allocated = self.allocated_spin.value()
        t.is_periodic = self.periodic_cb.isChecked()
        t.period_type = self.period_type_combo.currentText() if t.is_periodic else None

        if t.period_type == "Неделя":
            t.period_value = self.weekday_combo.currentText()
        elif t.period_type == "Месяц":
            t.period_value = self.month_day_spin.value()
        else:
            t.period_value = None

        t.deadline = (
            self.deadline_edit.dateTime().toPyDateTime()
            if self.use_deadline_cb.isChecked()
            else None
        )
        return t
