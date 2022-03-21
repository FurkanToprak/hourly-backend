from scheduling.schedule import Schedule
from scheduling.task import TaskItem

sched = Schedule()
task = TaskItem("school", "learn", "idk", 4, 96, [], "0")
blocks = sched.schedule_task(task)
print(sched.time_slots)
