# translations.py

LANGUAGES = ["Русский", "English"]


class Translation:
    def __init__(self):
        self.lang = "Русский"
        self.translations = {
            "Русский": {
                "Add": "Добавить",
                "Edit": "Редактировать",
                "Delete": "Удалить",
                "Settings": "Настройки",
                "Tasks": "Задачи",
                "Reports": "Графики",
                "Use Pomodoro": "Использовать Pomodoro-режим",
                "Settings info": "Настройки приложения",
                "Use dark theme": "Использовать тёмную тему",
                "Search task...": "Поиск задачи...",
                "From:": "С:",
                "To:": "По:",
                "Period:": "Период:",
                "Day": "День",
                "Week": "Неделя",
                "Month": "Месяц",
                "Build chart": "Построить график",
                "Allocated": "Выделено",
                "Spent": "Затрачено",
                "No data for selected period.": "Нет данных для выбранного периода.",
                "Hours": "Часы",
            },
            "English": {
                "Add": "Add",
                "Edit": "Edit",
                "Delete": "Delete",
                "Settings": "Settings",
                "Tasks": "Tasks",
                "Reports": "Reports",
                "Use Pomodoro": "Use Pomodoro",
                "Settings info": "Application settings",
                "Use dark theme": "Use dark theme",
                "Search task...": "Search task...",
                "From:": "From:",
                "To:": "To:",
                "Period:": "Period:",
                "Day": "Day",
                "Week": "Week",
                "Month": "Month",
                "Build chart": "Build chart",
                "Allocated": "Allocated",
                "Spent": "Spent",
                "No data for selected period.": "No data for selected period.",
                "Hours": "Hours",
            },
        }

    def set_language(self, lang):
        if lang in LANGUAGES:
            self.lang = lang

    def __call__(self, text):
        return self.translations.get(self.lang, {}).get(text, text)


# глобальный экземпляр для импорта
tr = Translation()
