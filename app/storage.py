import json
import os
from typing import List
from .models import Task

FILE = "tasks.json"


def load_tasks() -> List[Task]:
    if not os.path.exists(FILE):
        return []
    try:
        with open(FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return []
    tasks = []
    for item in data:
        try:
            t = Task.from_dict(item)
            tasks.append(t)
        except Exception:
            continue
    return tasks


def save_tasks(tasks: List[Task]):
    data = [t.to_dict() for t in tasks]
    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


SETTINGS_FILE = os.path.join(os.path.dirname(__file__), "settings.json")


def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        return {"language": "Русский", "dark_theme": True, "font_size": 12}

    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, dict):
                raise ValueError
            return data
    except Exception:
        # если файл повреждён — восстанавливаем дефолт
        return {"language": "Русский", "dark_theme": True, "font_size": 12}


def save_settings(settings):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)
