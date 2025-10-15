from datetime import datetime


class Session:
    def __init__(self, start=None, end=None):
        self.start = start or datetime.now()
        self.end = end


class Task:
    def __init__(
        self,
        id,
        title,
        description="",
        deadline=None,
        repeat=None,
        use_pomodoro=False,
        time_allocated=0,
        pomodoro_work=25,
        pomodoro_break=5,
    ):
        self.id = id
        self.title = title
        self.description = description
        self.deadline = deadline
        self.repeat = repeat
        self.is_completed = False
        self.use_pomodoro = use_pomodoro
        self.time_allocated = time_allocated
        self.pomodoro_work = pomodoro_work
        self.pomodoro_break = pomodoro_break
        self.sessions = []

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "use_pomodoro": self.use_pomodoro,
            "pomodoro_work": self.pomodoro_work,
            "pomodoro_break": self.pomodoro_break,
            "periodicity": self.periodicity,
            "deadline_enabled": self.deadline_enabled,
            "time_allocated": self.time_allocated,
            "sessions": [
                {
                    "start": s.start.isoformat(),
                    "end": s.end.isoformat() if s.end else None,
                }
                for s in self.sessions
            ],
        }

    @classmethod
    def from_dict(cls, data):
        from datetime import datetime

        sessions = []
        for s in data.get("sessions", []):
            start = datetime.fromisoformat(s["start"])
            end = datetime.fromisoformat(s["end"]) if s.get("end") else None
            sessions.append(type("Session", (), {"start": start, "end": end})())
        deadline = (
            datetime.fromisoformat(data["deadline"]).date()
            if data.get("deadline")
            else None
        )
        return cls(
            id=data.get("id"),
            title=data.get("title"),
            description=data.get("description", ""),
            deadline=deadline,
            is_completed=data.get("is_completed", False),
            use_pomodoro=data.get("use_pomodoro", False),
            pomodoro_work=data.get("pomodoro_work", 25),
            pomodoro_break=data.get("pomodoro_break", 5),
            periodicity=data.get("periodicity"),
            deadline_enabled=data.get("deadline_enabled", False),
            time_allocated=data.get("time_allocated", 0),
            sessions=sessions,
        )

    def is_overdue(self):
        """Возвращает True, если задача с дедлайном и он прошёл."""
        if not self.deadline:
            return False
        return (not self.is_completed) and (self.deadline < datetime.now().date())
