import json, os
from typing import List
from .models import Task, Session
from datetime import datetime

FILE = "tasks.json"


def load_tasks() -> List[Task]:
    if not os.path.exists(FILE):
        return []
    with open(FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    tasks = []
    for t in data:
        sessions = [
            Session(
                datetime.fromisoformat(s["start"]),
                datetime.fromisoformat(s["end"]) if s["end"] else None,
            )
            for s in t.get("sessions", [])
        ]
        task = Task(
            id=t["id"],
            title=t["title"],
            description=t.get("description", ""),
            comment=t.get("comment", ""),
            start_date=datetime.fromisoformat(t["start_date"]),
            deadline=(
                datetime.fromisoformat(t["deadline"]) if t.get("deadline") else None
            ),
            is_completed=t.get("is_completed", False),
            time_allocated=t.get("time_allocated", 60),
            time_spent=t.get("time_spent", 0),
            is_periodic=t.get("is_periodic", False),
            period_type=t.get("period_type"),
            sessions=sessions,
        )
        tasks.append(task)
    return tasks


def save_tasks(tasks: List[Task]):
    data = []
    for t in tasks:
        data.append(
            {
                "id": t.id,
                "title": t.title,
                "description": t.description,
                "comment": t.comment,
                "start_date": t.start_date.isoformat(),
                "deadline": t.deadline.isoformat() if t.deadline else None,
                "is_completed": t.is_completed,
                "time_allocated": t.time_allocated,
                "time_spent": t.time_spent,
                "is_periodic": t.is_periodic,
                "period_type": t.period_type,
                "sessions": [
                    {
                        "start": s.start.isoformat(),
                        "end": s.end.isoformat() if s.end else None,
                    }
                    for s in t.sessions
                ],
            }
        )
    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
