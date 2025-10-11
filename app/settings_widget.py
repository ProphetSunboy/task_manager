from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QCheckBox,
)
from PyQt5.QtCore import Qt
from .translations import LANGUAGES, tr
from .storage import load_settings, save_settings


class SettingsWidget(QWidget):
    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.settings = load_settings()  # загрузка текущих настроек
        self.init_ui()
        self.apply_font_size()  # сразу применяем шрифт

    def init_ui(self):
        layout = QVBoxLayout(self)

        # ----------------- Язык -----------------
        lang_layout = QHBoxLayout()
        self.lang_label = QLabel(tr("Язык") + ":")
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(LANGUAGES)
        current_lang = self.settings.get("language", "Русский")
        self.lang_combo.setCurrentText(current_lang)
        self.lang_combo.currentTextChanged.connect(self.change_language)
        lang_layout.addWidget(self.lang_label)
        lang_layout.addWidget(self.lang_combo)
        layout.addLayout(lang_layout)

        # ----------------- Тёмная тема -----------------
        theme_layout = QHBoxLayout()
        self.dark_theme_cb = QCheckBox(tr("Использовать тёмную тему"))
        self.dark_theme_cb.setChecked(self.settings.get("dark_theme", True))
        self.dark_theme_cb.stateChanged.connect(self.change_theme)
        theme_layout.addWidget(self.dark_theme_cb)
        layout.addLayout(theme_layout)

        # ----------------- Информационная надпись -----------------
        self.info_label = QLabel(tr("Настройки приложения"))
        self.info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.info_label)

        layout.addStretch()

    def change_language(self, lang):
        self.settings["language"] = lang
        save_settings(self.settings)
        tr.set_language(lang)
        self.update_ui_texts()

    def change_theme(self, state):
        self.settings["dark_theme"] = state == Qt.Checked
        save_settings(self.settings)

    def update_ui_texts(self):
        self.lang_label.setText(tr("Язык") + ":")
        self.dark_theme_cb.setText(tr("Использовать тёмную тему"))
        self.info_label.setText(tr("Настройки приложения"))

        # Применяем размер шрифта
        self.apply_font_size()

        # Обновляем интерфейс MainWindow, если передан
        if self.main_window:
            self.main_window.retranslateUi()

    def apply_font_size(self):
        font_size = self.settings.get("font_size", 12)
        font = self.font()
        font.setPointSize(font_size)
        self.setFont(font)
