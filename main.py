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
from app.translations import tr


class NavButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setCheckable(True)
        self.setMinimumHeight(35)
        self.setStyleSheet(
            """
            QPushButton { font-size: 14px; padding: 8px 16px; border: none; border-radius: 6px; color: #ddd; background-color: transparent; }
            QPushButton:hover { background-color: rgba(255,255,255,0.05); }
            QPushButton:checked { background-color: #3a86ff; color: white; font-weight: bold; }
        """
        )


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Timely — Трекер времени")
        self.setMinimumSize(900, 600)

        self.container = QWidget()
        self.main_layout = QVBoxLayout(self.container)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.nav_bar = QHBoxLayout()
        self.nav_bar.setContentsMargins(10, 10, 10, 10)
        self.nav_bar.setSpacing(8)

        self.btn_tasks = NavButton("")
        self.btn_reports = NavButton("")
        self.btn_settings = NavButton("")

        self.nav_bar.addWidget(self.btn_tasks)
        self.nav_bar.addWidget(self.btn_reports)
        self.nav_bar.addWidget(self.btn_settings)
        self.nav_bar.addStretch()

        self.stack = QStackedWidget()
        self.tasks_page = TasksWidget()
        self.reports_page = ReportsWidget()
        self.settings_page = SettingsWidget(main_window=self)

        self.stack.addWidget(self.tasks_page)
        self.stack.addWidget(self.reports_page)
        self.stack.addWidget(self.settings_page)

        self.main_layout.addLayout(self.nav_bar)
        self.main_layout.addWidget(self.stack)
        self.setCentralWidget(self.container)

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

    def closeEvent(self, event):
        # перед закрытием делегируем TasksWidget сохранение
        if hasattr(self, "tasks_page") and self.tasks_page:
            self.tasks_page.closeEvent(event)
        event.accept()

    def retranslateUi(self):
        self.btn_tasks.setText(tr("Tasks"))
        self.btn_reports.setText(tr("Reports"))
        self.btn_settings.setText(tr("Settings"))
        # перекладываем перевод для всех дочерних виджетов
        if hasattr(self.tasks_page, "retranslateUi"):
            self.tasks_page.retranslateUi()
        if hasattr(self.reports_page, "retranslateUi"):
            self.reports_page.retranslateUi()
        if hasattr(self.settings_page, "retranslateUi"):
            self.settings_page.retranslateUi()


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
