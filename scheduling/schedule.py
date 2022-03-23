from tasks import tasks_routes
from users import user_routes
import datetime
import itertools
from dateutil import parser

# each time unit is 15 minutes
TIME_UNIT = 30
UNITS_PER_DAY = int((24 * 60 / TIME_UNIT)) * 2
CURRENT_TIME = datetime.datetime.utcnow()


class Schedule:
    def __init__(self, user_id) -> None:
        self.time_slots = None
        self.user_id = user_id
        self.tasks = []
        self.last_task = None
        self.num_days = 0
        self.schedule_tasks()

    def generate_priority(self, estimated_time, completed_time, deadline) -> float:
        priority = (float(estimated_time) - float(completed_time)) / (
            (parser.parse(deadline) - CURRENT_TIME).total_seconds() / 3600
        )
        return priority

    def schedule_tasks(self):
        self.tasks = tasks_routes.get_task({"id": self.user_id})
        self.last_task = parser.parse(
            max(self.tasks, key=lambda x: parser.parse(x["due_date"]))
        )

        # self.time_slots = (self.last_task - CURRENT_TIME).days * UNITS_PER_DAY * [None]
        self.num_days = (self.last_task - CURRENT_TIME).days

        self.time_slots = {}
        for i in range(self.num_days):
            date = datetime.now().date() + datetime.timedelta(days=i)
            self.time_slots[date] = UNITS_PER_DAY * [None]

        self.schedule_events()

    def schedule_events(self) -> list:
        sleep_times = user_routes.get_sleep(self.user_id)
        start_units, end_units = self._parse_sleep_time(
            sleep_times["startOfDay"], sleep_times["endOfDay"]
        )

        for i in range(self.num_days):
            date = datetime.now().date() + datetime.timedelta(days=i)
            self.time_slots[date][0:start_units] = itertools.repeat(
                "SLEEP", (start_units)
            )
            self.time_slots[date][end_units:] = itertools.repeat(
                "SLEEP", (UNITS_PER_DAY - end_units)
            )

    def define_blocks(self):
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

    def _parse_sleep_time(self, start_time, end_time):
        start_time = parser.parse(start_time)
        start_time = self._round_time(start_time, True)

        end_time = parser.parse(end_time)
        end_time = self._round_time(end_time, False)

        start_units, end_units = self._dt_to_units(start_time, end_time)

        return start_units, end_units

    def _round_time(self, time, round_up):
        if round_up:
            if 0 <= time.minute <= 30:
                time = time.replace(minute=30)
            else:
                time = time + datetime.timedelta(hours=1)
                time = time.replace(minute=0)
        else:
            if 0 <= time.minute <= 30:
                time = time.replace(minute=0)
            else:
                time = time.replace(minute=30)

        return time

    def _dt_to_units(self, start_time, end_time):
        start_units = (start_time.hour * 60 + start_time.minute) / TIME_UNIT
        end_delta = (end_time + datetime.timedelta(days=1)).replace(
            hour=0, minute=0
        ) - end_time
        end_units = int(end_delta.total_seconds() / 60) / TIME_UNIT

        return start_units, end_units
