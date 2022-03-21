class TimeBlock:
    def __init__(
        self,
        name: str,
        task: str,
        start: int,
        end: int,
        repeats: str,
        all_day: bool,
        blocker: bool,
    ) -> None:
        self.name = name
        self.task = task
        self.start = start
        self.end = end
        self.repeats = repeats
        self.all_day = all_day
        self.blocker = blocker
