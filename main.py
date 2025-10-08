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
        self.setWindowTitle("ProjectX — Трекер времени")
        self.setMinimumSize(900, 600)

        container = QWidget()
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        nav_bar = QHBoxLayout()
        nav_bar.setContentsMargins(10, 10, 10, 10)
        nav_bar.setSpacing(8)
        self.btn_tasks = NavButton("📝 Задачи")
        self.btn_reports = NavButton("📊 Графики")
        self.btn_settings = NavButton("⚙️ Настройки")
        nav_bar.addWidget(self.btn_tasks)
        nav_bar.addWidget(self.btn_reports)
        nav_bar.addWidget(self.btn_settings)
        nav_bar.addStretch()

        self.stack = QStackedWidget()
        self.tasks_page = TasksWidget()
        self.reports_page = ReportsWidget()
        self.settings_page = SettingsWidget()

        self.stack.addWidget(self.tasks_page)
        self.stack.addWidget(self.reports_page)
        self.stack.addWidget(self.settings_page)

        main_layout.addLayout(nav_bar)
        main_layout.addWidget(self.stack)
        self.setCentralWidget(container)

        self.btn_tasks.clicked.connect(lambda: self.switch_page(0))
        self.btn_reports.clicked.connect(lambda: self.switch_page(1))
        self.btn_settings.clicked.connect(lambda: self.switch_page(2))

        self.switch_page(0)

    def switch_page(self, index):
        self.stack.setCurrentIndex(index)
        self.btn_tasks.setChecked(index == 0)
        self.btn_reports.setChecked(index == 1)
        self.btn_settings.setChecked(index == 2)


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
