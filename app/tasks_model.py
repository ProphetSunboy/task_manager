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
    ):
        self.id = id
        self.title = title
        self.description = description
        self.deadline = deadline
        self.repeat = repeat
        self.use_pomodoro = use_pomodoro
        self.time_allocated = time_allocated
        self.sessions = []
