import json
import os
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QSpinBox, QApplication

SETTINGS_FILE = os.path.join(os.path.dirname(__file__), "settings.json")


class SettingsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        layout.addWidget(QLabel("Размер шрифта:"))

        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 24)  # ограничения
        layout.addWidget(self.font_size_spin)

        # при изменении размера шрифта сразу применяем
        self.font_size_spin.valueChanged.connect(self.apply_font_size)

        self.load_settings()

    def load_settings(self):
        """Загрузить размер шрифта из settings.json"""
        size = 10
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    size = data.get("font_size", 10)
            except Exception:
                pass
        self.font_size_spin.setValue(size)
        self.apply_font_size(size)

    def save_settings(self, size):
        """Сохраняем размер шрифта"""
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump({"font_size": size}, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def apply_font_size(self, size=None):
        """Применяем размер шрифта ко всему приложению и диалогам"""
        if size is None:
            size = self.font_size_spin.value()

        font = QApplication.instance().font()
        font.setPointSize(size)
        QApplication.instance().setFont(font)

        # Применяем к уже существующим виджетам и диалогам
        for w in QApplication.instance().allWidgets():
            w.setFont(font)
            w.setStyleSheet(
                f"""
                QLabel, QLineEdit, QTextEdit, QCheckBox, QSpinBox {{
                    font-size: {size}pt;
                }}
            """
            )

        self.save_settings(size)


def apply_font_to_dialog(dialog: QWidget):
    """Вызывать для любого нового диалога после создания"""
    font = QApplication.instance().font()
    dialog.setFont(font)
    for child in dialog.findChildren(QWidget):
        child.setFont(font)
    dialog.setStyleSheet(
        f"""
        QLabel, QLineEdit, QTextEdit, QCheckBox, QSpinBox {{
            font-size: {font.pointSize()}pt;
        }}
    """
    )
