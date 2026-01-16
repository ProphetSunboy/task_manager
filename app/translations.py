LANGUAGES = ["Русский", "English"]


class Translation:
    def __init__(self):
        # язык по-умолчанию
        self.lang = "Русский"
        # словарь переводов
        self.translations = {
            "Русский": {
                # навигация / основное
                "Tasks": "Задачи",
                "Reports": "Графики",
                "Settings": "Настройки",
                "Timely — Time Tracker": "Timely — Трекер времени",
                # tasks_widget
                "Add": "Добавить",
                "Edit": "Редактировать",
                "Delete": "Удалить",
                "Start": "Старт",
                "Stop": "Стоп",
                "Select a task": "Выберите задачу",
                "Generation of AI advice...": "Генерация ИИ совета...",
                "Generate for all tasks": "Сгенерировать для всех задач",
                "Tracking": "Трекинг",
                "History:": "История:",
                "Info": "Инфо",
                "Delete task": "Удалить задачу",
                "Select a task:": "Выберите задачу:",
                "Today": "Сегодня",
                "Week": "Неделя",
                "Total": "Всего",
                "Enable Deadline": "Включить дедлайн",
                "Repeat:": "Повторять:",
                "None": "Нет",
                "Daily": "Ежедневно",
                "Weekly": "Еженедельно",
                "Monthly": "Ежемесячно",
                "Title:": "Название:",
                "Description:": "Описание:",
                "Work minutes:": "Время работы:",
                "Break minutes:": "Время перерыва:",
                "Allocated time (min):": "Выделенное время (мин):",
                "Task completed": "Задача выполнена",
                "OK": "ОК",
                "Cancel": "Отмена",
                # pomodoro / generic
                "Work": "Работа",
                "Break": "Перерыв",
                "Cycles before long break:": "Циклов до длинного перерыва:",
                "Use Pomodoro": "Помодоро",
                # reports_widget
                "Search task...": "Поиск задачи...",
                "From:": "С:",
                "To:": "По:",
                "Period:": "Период:",
                "Day": "День",
                "Week": "Неделя",
                "Month": "Месяц",
                "Build chart": "Построить график",
                "No data for selected period.": "Нет данных для выбранного периода.",
                "Total": "Общее время",
                "Allocated": "Выделено",
                "Spent": "Затрачено",
                "Hours": "Часы",
                "Report for task:": "Отчёт по задаче:",
                "Select a task:": "Выберите задачу:",
                # settings
                "Language": "Язык",
                "Use dark theme": "Использовать тёмную тему",
                "Font size": "Размер шрифта",
            },
            "English": {
                # навигация / основное
                "Tasks": "Tasks",
                "Reports": "Reports",
                "Settings": "Settings",
                "Timely — Time Tracker": "Timely — Time Tracker",
                # tasks_widget
                "Add": "Add",
                "Edit": "Edit",
                "Delete": "Delete",
                "Start": "Start",
                "Stop": "Stop",
                "Select a task": "Select a task",
                "Generation of AI advice...": "Generation of AI advice...",
                "Generate for all tasks": "Generate for all tasks",
                "Tracking": "Tracking",
                "History:": "History:",
                "Info": "Info",
                "Delete task": "Delete task",
                "Select a task:": "Select a task:",
                "Today": "Today",
                "Week": "Week",
                "Total": "Total",
                "Enable Deadline": "Enable Deadline",
                "Repeat:": "Repeat:",
                "None": "None",
                "Daily": "Daily",
                "Weekly": "Weekly",
                "Monthly": "Monthly",
                "Title:": "Title:",
                "Description:": "Description:",
                "Work minutes:": "Work minutes:",
                "Break minutes:": "Break minutes:",
                "Allocated time (min):": "Allocated time (min):",
                "Task completed": "Task completed",
                "OK": "OK",
                "Cancel": "Cancel",
                # pomodoro / generic
                "Work": "Work",
                "Break": "Break",
                "Cycles before long break:": "Cycles before long break:",
                "Use Pomodoro": "Use Pomodoro",
                # reports_widget
                "Search task...": "Search task...",
                "From:": "From:",
                "To:": "To:",
                "Period:": "Period:",
                "Day": "Day",
                "Week": "Week",
                "Month": "Month",
                "Build chart": "Build chart",
                "No data for selected period.": "No data for selected period.",
                "Total": "Total",
                "Allocated": "Allocated",
                "Spent": "Spent",
                "Hours": "Hours",
                "Report for task:": "Report for task:",
                "Select a task:": "Select a task:",
                # settings
                "Language": "Language",
                "Use dark theme": "Use dark theme",
                "Font size": "Font size",
            },
        }

    def set_language(self, lang):
        if lang in LANGUAGES:
            self.lang = lang

    def __call__(self, text):
        return self.translations.get(self.lang, {}).get(text, text)


tr = Translation()
