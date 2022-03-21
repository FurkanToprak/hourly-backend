from scheduling.task import TaskItem
from scheduling.block import TimeBlock

# each time unit is 15 minutes
TIME_UNIT = 60 * 15
UNITS_PER_DAY = int((24 * 60 * 60 / TIME_UNIT))
CURRENT_TIME = 0
TIME_QUANTUM = 4


class Schedule:
    def __init__(self) -> None:
        self.time_slots = [None] * UNITS_PER_DAY

    def generate_priority(self, task: TaskItem) -> float:
        priority = task.estimated_time / (task.deadline - CURRENT_TIME)
        return priority

    def schedule_task(self, task: TaskItem):
        pass

    def schedule_tasks(self, tasks: list):
        pass

    def schedule_block(self, task: TaskItem) -> list:
        blocks = []

        # find empty start time in time_slots list
        for start in range(CURRENT_TIME, UNITS_PER_DAY):
            for i in range(0, TIME_QUANTUM):
                if self.time_slots[start + i] != None:
                    continue
            break

        end = start + TIME_QUANTUM
        block = TimeBlock(task.name, task.id, start, end, "nah", False, False)
        blocks.append(block)

        for i in range(start, end):
            self.time_slots[i] = block.task

        return blocks
