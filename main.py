# main.py
import sys
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QStackedWidget,
)
import qdarkstyle
from app.tasks_widget import TasksWidget
from app.reports_widget import ReportsWidget
from app.settings_widget import SettingsWidget
from app.storage import load_settings
from app.translations import tr


class NavButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setCheckable(True)
        self.setMinimumHeight(35)
        self.extra_width = 20
        # чуть поменьше padding, чтобы помещалось
        self.setStyleSheet(
            """
            QPushButton { padding: 6px 10px; border: none; border-radius: 6px; color: #ddd; background-color: transparent; }
            QPushButton:hover { background-color: rgba(255,255,255,0.05); }
            QPushButton:checked { background-color: #3a86ff; color: white; font-weight: bold; }
        """
        )

    def setFont(self, font):
        """Переопределяем setFont, чтобы кнопка подгонялась под размер текста"""
        super().setFont(font)
        metrics = self.fontMetrics()
        text_width = metrics.horizontalAdvance(self.text()) + 20  # базовый запас
        text_height = metrics.height() + 12

        # если кнопка выделена, добавляем небольшой запас
        if self.isChecked():
            text_width += self.extra_width

        self.setMinimumWidth(text_width)
        self.setMinimumHeight(text_height)

    def setChecked(self, checked: bool):
        """При смене состояния checked тоже пересчитываем ширину"""
        super().setChecked(checked)
        self.setFont(self.font())  # пересчёт ширины для жирного текста


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # загружаем настройки (шрифт/язык) и передаём дальше
        self.settings = load_settings()

        self.setWindowTitle(tr("Timely — Time Tracker"))
        self.setMinimumSize(900, 600)

        container = QWidget()
        self.main_layout = QVBoxLayout(container)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        nav_bar = QHBoxLayout()
        nav_bar.setContentsMargins(10, 10, 10, 10)
        nav_bar.setSpacing(8)
        self.btn_tasks = NavButton("")
        self.btn_reports = NavButton("")
        self.btn_settings = NavButton("")
        nav_bar.addWidget(self.btn_tasks)
        nav_bar.addWidget(self.btn_reports)
        nav_bar.addWidget(self.btn_settings)
        nav_bar.addStretch()

        self.stack = QStackedWidget()
        # передаём settings в страницы, чтобы они могли читать font_size и т.д.
        self.tasks_page = TasksWidget(settings=self.settings)
        self.reports_page = ReportsWidget(settings=self.settings)
        self.settings_page = SettingsWidget(main_window=self, settings=self.settings)

        self.stack.addWidget(self.tasks_page)
        self.stack.addWidget(self.reports_page)
        self.stack.addWidget(self.settings_page)

        self.main_layout.addLayout(nav_bar)
        self.main_layout.addWidget(self.stack)
        self.setCentralWidget(container)

        self.btn_tasks.clicked.connect(lambda: self.switch_page(0))
        self.btn_reports.clicked.connect(lambda: self.switch_page(1))
        self.btn_settings.clicked.connect(lambda: self.switch_page(2))

        self.switch_page(0)
        self.retranslateUi()

    def switch_page(self, index):
        self.stack.setCurrentIndex(index)
        self.btn_tasks.setChecked(index == 0)
        self.btn_reports.setChecked(index == 1)
        self.btn_settings.setChecked(index == 2)

        if index == 1:
            self.reports_page.refresh_data()

    def closeEvent(self, event):
        # перед закрытием делегируем TasksWidget сохранение
        if hasattr(self, "tasks_page") and self.tasks_page:
            self.tasks_page.closeEvent(event)
        event.accept()

    def retranslateUi(self):
        # обновляем заголовок окна
        self.setWindowTitle(tr("Timely — Time Tracker"))
        # nav buttons: короткий текст + tooltip с полным названием
        self.btn_tasks.setText(tr("Tasks"))
        self.btn_tasks.setToolTip(tr("Tasks"))
        self.btn_reports.setText(tr("Reports"))
        self.btn_reports.setToolTip(tr("Reports"))
        self.btn_settings.setText(tr("Settings"))
        self.btn_settings.setToolTip(tr("Settings"))

        font = QApplication.instance().font()
        self.btn_tasks.setFont(font)
        self.btn_reports.setFont(font)
        self.btn_settings.setFont(font)

        # переотложим переводы для страниц (если у них есть retranslateUi)
        if hasattr(self.tasks_page, "retranslateUi"):
            self.tasks_page.retranslateUi()
        if hasattr(self.reports_page, "retranslateUi"):
            # необходимо также обновить список задач в графиках
            self.reports_page.retranslateUi()
            self.reports_page.populate_task_list()
        if hasattr(self.settings_page, "retranslateUi"):
            self.settings_page.retranslateUi()

    def update_nav_buttons_font(self):
        """Применяет текущий глобальный шрифт к nav buttons (их шрифт может не обновиться автоматически)."""
        app = QApplication.instance()
        if not app:
            return
        font = app.font()
        try:
            # применяем шрифт явно к кнопкам навигации
            self.btn_tasks.setFont(font)
            self.btn_reports.setFont(font)
            self.btn_settings.setFont(font)
        except Exception:
            pass

    def update_nav_style(self, dark: bool):
        """Обновляет цвет текста навигационных кнопок в зависимости от темы."""
        # подбираем цвет текста, чтобы было читабельно на фоне темы
        if dark:
            text_color = "#ffffff"
            # оставляем фон прозрачным — qdarkstyle сделает остальное
            btn_bg = "transparent"
        else:
            text_color = "#111111"
            btn_bg = "transparent"

        # обновляем стиль кнопок навигации — только цвет текста и hover
        style = f"""
            QPushButton {{ color: {text_color}; background-color: {btn_bg}; }}
            QPushButton:hover {{ background-color: rgba(0,0,0,0.06); }}
            QPushButton:checked {{ background-color: #3a86ff; color: white; }}
        """
        try:
            self.btn_tasks.setStyleSheet(style)
            self.btn_reports.setStyleSheet(style)
            self.btn_settings.setStyleSheet(style)
        except Exception:
            pass


def main():
    app = QApplication(sys.argv)
    # Загружаем настройки
    settings = load_settings()
    dark_theme = settings.get("dark_theme", True)

    # Применяем тему сразу
    if dark_theme:
        try:
            app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
        except Exception:
            app.setStyleSheet("")
    else:
        app.setStyleSheet("")
    # если в настройках был размер шрифта — применим
    # но SettingsWidget также применит при инициализации
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
