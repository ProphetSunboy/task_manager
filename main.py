import sys
import json
import time
import os
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import QTimer
import qdarkstyle


class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        # Загружаем .ui напрямую
        uic.loadUi("main_window.ui", self)

        # Внутренние переменные
        self.start_time = None
        self.elapsed_time = 0
        self.timer_running = False

        # QTimer для обновления каждую секунду
        self.qtimer = QTimer()
        self.qtimer.timeout.connect(self.update_timer)

        # Кнопка старт/стоп
        self.btn_start.clicked.connect(self.toggle_timer)

        # Проверим файл для задач
        if not os.path.exists("tasks.json"):
            with open("tasks.json", "w", encoding="utf-8") as f:
                json.dump([], f)

    def toggle_timer(self):
        if not self.timer_running:
            # Запускаем
            self.start_time = time.time()
            self.timer_running = True
            self.btn_start.setText("Стоп")
            self.qtimer.start(1000)
        else:
            # Останавливаем
            self.timer_running = False
            self.qtimer.stop()
            self.elapsed_time += int(time.time() - self.start_time)
            self.save_task(self.elapsed_time)
            self.btn_start.setText("Старт")

    def update_timer(self):
        current_time = int(time.time() - self.start_time) + self.elapsed_time
        self.label_timer.setText(self.format_time(current_time))

    def save_task(self, seconds):
        """Сохраняем задачу в tasks.json"""
        try:
            with open("tasks.json", "r", encoding="utf-8") as f:
                tasks = json.load(f)
        except Exception:
            tasks = []

        if tasks:
            tasks[0]["time_spent"] += seconds
        else:
            tasks.append({"id": 1, "title": "Моя задача", "time_spent": seconds})

        with open("tasks.json", "w", encoding="utf-8") as f:
            json.dump(tasks, f, ensure_ascii=False, indent=2)

    @staticmethod
    def format_time(seconds):
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        return f"{h:02}:{m:02}:{s:02}"


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    window = MainApp()
    window.show()
    sys.exit(app.exec_())
