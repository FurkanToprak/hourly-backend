class TaskItem:
    def __init__(
        self,
        name: str,
        description: str,
        label: str,
        estimated_time: int,
        deadline: int,
        scheduled: list,
        id: str,
    ) -> None:
        self.name = name
        self.description = description
        self.label = label
        self.estimated_time = estimated_time
        self.deadline = deadline
        self.scheduled = scheduled
        self.id = id
