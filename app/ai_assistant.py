# ai_assistant.py
from .models import Task
from datetime import datetime, date


def get_task_advice(task: Task) -> str:
    advices = []
    if not task.is_completed:
        if task.deadline:
            if isinstance(task.deadline, datetime):
                deadline_date = task.deadline.date()
            elif isinstance(task.deadline, date):
                deadline_date = task.deadline
            else:
                deadline_date = None

            if deadline_date:
                days_left = (deadline_date - datetime.now().date()).days
            else:
                days_left = None

            if days_left < 0:
                advices.append("Задача просрочена!")
            elif days_left <= 2:
                advices.append("Дедлайн близко, срочно выполните задачу")
        if getattr(task, "use_pomodoro", False):
            advices.append(
                f"Pomodoro: {task.pomodoro_work} мин работы / {task.pomodoro_break} мин перерыва"
            )
        if task.time_spent < task.time_allocated / 2:
            advices.append("Вы ещё не сильно продвинулись — планируйте время")
    else:
        advices.append("Задача выполнена — отличная работа!")
    return "\n".join(advices) if advices else "Нет рекомендаций"


def get_all_tasks_advice(tasks: list[Task]) -> str:
    advices = []
    for task in tasks:
        advice = get_task_advice(task)
        advices.append(f"{task.title or '(no title)'}:\n{advice}")
    return "\n\n".join(advices)
