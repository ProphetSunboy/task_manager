import json
import uuid
from datetime import datetime
from typing import Optional, List


class Session:
    def __init__(self, start: datetime, end: Optional[datetime] = None):
        self.start = start
        self.end = end

    def to_dict(self):
        return {
            "start": self.start.isoformat(),
            "end": self.end.isoformat() if self.end else None,
        }

    @classmethod
    def from_dict(cls, data):
        start = datetime.fromisoformat(data["start"])
        end = datetime.fromisoformat(data["end"]) if data.get("end") else None
        return cls(start=start, end=end)


class Task:
    def __init__(
        self,
        id: Optional[str],
        title: str,
        description: str = "",
        comment: str = "",
        start_date: Optional[datetime] = None,
        deadline: Optional[datetime] = None,
        is_completed: bool = False,
        time_allocated: int = 60,
        time_spent: int = 0,
        is_periodic: bool = False,
        period_type: Optional[str] = None,
        sessions: Optional[List[Session]] = None,
        # Pomodoro settings
        use_pomodoro: bool = False,
        pomodoro_work: int = 25,
        pomodoro_break: int = 5,
        pomodoro_long: int = 15,
        pomodoro_cycles: int = 4,
    ):
        self.id = id or str(uuid.uuid4())
        self.title = title
        self.description = description
        self.comment = comment
        self.start_date = start_date or datetime.now()
        self.deadline = deadline
        self.is_completed = is_completed
        self.time_allocated = time_allocated
        self.time_spent = time_spent
        self.is_periodic = is_periodic
        self.period_type = period_type
        self.sessions = sessions or []

        # Pomodoro
        self.use_pomodoro = use_pomodoro
        self.pomodoro_work = pomodoro_work
        self.pomodoro_break = pomodoro_break
        self.pomodoro_long = pomodoro_long
        self.pomodoro_cycles = pomodoro_cycles

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "comment": self.comment,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "is_completed": self.is_completed,
            "time_allocated": self.time_allocated,
            "time_spent": self.time_spent,
            "is_periodic": self.is_periodic,
            "period_type": self.period_type,
            "sessions": [s.to_dict() for s in self.sessions],
            # Pomodoro
            "use_pomodoro": self.use_pomodoro,
            "pomodoro_work": self.pomodoro_work,
            "pomodoro_break": self.pomodoro_break,
            "pomodoro_long": self.pomodoro_long,
            "pomodoro_cycles": self.pomodoro_cycles,
        }

    @classmethod
    def from_dict(cls, data):
        start_date = (
            datetime.fromisoformat(data["start_date"])
            if data.get("start_date")
            else None
        )
        deadline = (
            datetime.fromisoformat(data["deadline"]) if data.get("deadline") else None
        )
        sessions_data = data.get("sessions", [])
        sessions = [Session.from_dict(s) for s in sessions_data]
        return cls(
            id=data.get("id"),
            title=data.get("title", ""),
            description=data.get("description", ""),
            comment=data.get("comment", ""),
            start_date=start_date,
            deadline=deadline,
            is_completed=data.get("is_completed", False),
            time_allocated=data.get("time_allocated", 60),
            time_spent=data.get("time_spent", 0),
            is_periodic=data.get("is_periodic", False),
            period_type=data.get("period_type"),
            sessions=sessions,
            use_pomodoro=data.get("use_pomodoro", False),
            pomodoro_work=data.get("pomodoro_work", 25),
            pomodoro_break=data.get("pomodoro_break", 5),
            pomodoro_long=data.get("pomodoro_long", 15),
            pomodoro_cycles=data.get("pomodoro_cycles", 4),
        )

    def is_overdue(self) -> bool:
        from datetime import datetime, date

        if not self.deadline:
            return False

        # Приводим к date
        if isinstance(self.deadline, datetime):
            deadline_date = self.deadline.date()
        else:
            deadline_date = self.deadline

        return (not self.is_completed) and (deadline_date < datetime.now().date())
