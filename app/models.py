from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class Session:
    start: datetime
    end: Optional[datetime] = None


@dataclass
class Task:
    id: str
    title: str
    description: str = ""
    comment: str = ""
    start_date: datetime = field(default_factory=datetime.now)
    deadline: Optional[datetime] = None
    is_completed: bool = False
    time_allocated: int = 60  # минуты
    time_spent: int = 0  # минуты
    is_periodic: bool = False
    period_type: Optional[str] = None
    sessions: List[Session] = field(default_factory=list)

    def is_overdue(self) -> bool:
        return (
            self.deadline and datetime.now() > self.deadline and not self.is_completed
        )
