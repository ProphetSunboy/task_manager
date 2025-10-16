# app/settings_widget.py
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QCheckBox,
    QPushButton,
    QApplication,
)
from PyQt5.QtCore import Qt
from .translations import LANGUAGES, tr
from .storage import load_settings, save_settings
import qdarkstyle


class SettingsWidget(QWidget):
    def __init__(self, main_window=None, settings=None):
        super().__init__()
        self.main_window = main_window
        # если settings передали — используем, иначе загружаем из файла
        self.settings = settings if settings is not None else load_settings()
        self.init_ui()
        # применяем шрифт глобально сразу
        self.apply_font_size()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # ----------------- Язык -----------------
        lang_layout = QHBoxLayout()
        self.lang_label = QLabel(tr("Language") + ":")
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(list(dict.fromkeys(LANGUAGES)))
        current_lang = self.settings.get("language", "Русский")
        # если сохранён язык — применяем
        self.lang_combo.setCurrentText(current_lang)
        self.lang_combo.currentTextChanged.connect(self.change_language)
        lang_layout.addWidget(self.lang_label)
        lang_layout.addWidget(self.lang_combo)
        layout.addLayout(lang_layout)

        # ----------------- Размер текста -----------------
        font_layout = QHBoxLayout()
        self.font_label = QLabel(tr("Размер шрифта") + ":")
        self.font_combo = QComboBox()
        for size in [10, 12, 14, 16, 18, 20]:
            self.font_combo.addItem(str(size))
        current_size = str(self.settings.get("font_size", 12))
        self.font_combo.setCurrentText(current_size)
        self.font_combo.currentTextChanged.connect(self.change_font_size)
        font_layout.addWidget(self.font_label)
        font_layout.addWidget(self.font_combo)
        layout.addLayout(font_layout)

        # ----------------- Тёмная тема -----------------
        theme_layout = QHBoxLayout()
        self.dark_theme_cb = QCheckBox(tr("Use dark theme"))
        self.dark_theme_cb.setChecked(self.settings.get("dark_theme", True))
        self.dark_theme_cb.stateChanged.connect(self.change_theme)
        theme_layout.addWidget(self.dark_theme_cb)
        layout.addLayout(theme_layout)

        layout.addStretch()

    def change_language(self, lang):
        # блокируем сигнал, чтобы избежать зацикливания
        self.lang_combo.blockSignals(True)

        if self.settings.get("language") == lang:
            self.lang_combo.blockSignals(False)
            return

        self.settings["language"] = lang
        save_settings(self.settings)

        tr.set_language(lang)
        self.retranslateUi()

        # если есть главное окно — обновляем и его тексты
        if self.main_window:
            self.main_window.retranslateUi()

        # возвращаем сигнал обратно
        self.lang_combo.blockSignals(False)

    def change_theme(self, state):
        """Переключает тему с использованием qdarkstyle"""
        self.settings["dark_theme"] = state == Qt.Checked
        save_settings(self.settings)
        self.apply_theme()

    def apply_theme(self):
        """Применяет qdarkstyle или сбрасывает его.
        Дополнительно обновляет стиль навигационных кнопок в main window."""
        app = QApplication.instance()
        if not app:
            return

        if self.settings.get("dark_theme", True):
            # используем qdarkstyle (работает по всему приложению)
            try:
                app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
            except Exception:
                # fallback если qdarkstyle неожиданно не работает
                app.setStyleSheet("")
        else:
            app.setStyleSheet("")

        # обновляем nav buttons (цвет/стиль) в main window, если есть
        if self.main_window and hasattr(self.main_window, "update_nav_style"):
            try:
                self.main_window.update_nav_style(
                    dark=self.settings.get("dark_theme", True)
                )
            except Exception:
                pass

    def save_settings(self):
        # сохраняет текущие настройки (в т.ч. font_size, если будет добавлено редактирование)
        save_settings(self.settings)
        # применим шрифт заново на случай изменения в файле
        self.apply_font_size()
        if self.main_window and hasattr(self.main_window, "retranslateUi"):
            self.main_window.retranslateUi()

    def retranslateUi(self):
        self.lang_label.setText(tr("Language") + ":")
        self.dark_theme_cb.setText(tr("Use dark theme"))
        self.font_label.setText(tr("Font size") + ":")
        # восстановим список языков и выбранный элемент (названия языков не переводим)
        current = self.lang_combo.currentText()
        self.lang_combo.clear()
        self.lang_combo.addItems(list(dict.fromkeys(LANGUAGES)))
        self.lang_combo.setCurrentText(current)
        # применяем шрифт (чтобы текст поместился)
        self.apply_font_size()

    def change_font_size(self, size_str):
        size = int(size_str)
        self.settings["font_size"] = size
        save_settings(self.settings)
        self.apply_font_size()
        if self.main_window:
            self.main_window.retranslateUi()

    def apply_font_size(self):
        """Применяет текущий размер шрифта ко всему приложению."""
        font_size = int(self.settings.get("font_size", 12))
        app = QApplication.instance()
        if app:
            font = app.font()
            font.setPointSize(font_size)
            app.setFont(font)
            try:
                for w in app.allWidgets():
                    w.setFont(font)
            except Exception:
                pass
        else:
            font = self.font()
            font.setPointSize(font_size)
            self.setFont(font)

        # обновляем nav buttons шрифт через main window метод — безопаснее напрямую менять main internals
        if self.main_window and hasattr(self.main_window, "update_nav_buttons_font"):
            try:
                self.main_window.update_nav_buttons_font()
            except Exception:
                pass
