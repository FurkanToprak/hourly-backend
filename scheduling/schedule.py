""" Auto Scheduling Algorithm"""
import datetime
import itertools
from dateutil import parser
import pytz
from tasks import tasks_routes
from users import user_routes
from events import events_routes
from blocks.models import Block
from blocks.blocks_routes import delete_blocks
from db_connection import database

TIME_UNIT = 30
UNITS_PER_DAY = int((24 * 60 / TIME_UNIT))
TIME_ZONE = pytz.timezone("America/Chicago")
CURRENT_TIME = (
    datetime.datetime.now(datetime.timezone.utc)
    .replace(tzinfo=pytz.utc)
    .astimezone(TIME_ZONE)
)


class Schedule:
    """Auto Scheduler Class"""

    def __init__(self, user_id) -> None:
        self.time_slots = None
        self.user_id = user_id
        self.tasks = []
        self.cram_tasks = []
        self.event_dict = {}
        self.num_days = 0
        self.batch_writes = 0

        self.scheduler_success = True

    def scheduler(self):
        """Main scheduling flow"""
        task_list = tasks_routes.get_task_scheduler(self.user_id)
        # List of Dictionaries (Tasks)
        # tasks/models.py
        self.tasks = [
            value for value in task_list.values() if not value["do_not_schedule"]
        ]

        # Rest of tasks that are marked for cramming
        self.cram_tasks = [
            value for value in task_list.values() if value["do_not_schedule"]
        ]

        # Sets self.num_days (days between now and last due date) value accordingly
        self.set_num_days()
        # Builds self.time_slots
        # Dictionary of Lists
        # self.time_slots[date] = [UNITS_PER_DAY Length List]
        # Specific Day - [integer (0-Units per day)] = Tuple of length 2
        # (None, None), ("SLEEP", None), ("TASK", task_dict), ("EVENT", "event_dict")
        self.build_time_slots()

        if len(self.tasks) == 0:
            self.write_events_and_sleep()
            delete_blocks(self.user_id)
            self.define_blocks()
        else:
            self.write_events_and_sleep()
            enough_time = self.schedule_tasks()

            if enough_time:
                delete_blocks(self.user_id)
                self.define_blocks()
            else:
                self.scheduler_success = False

    def set_num_days(self, manually_set=0):
        if manually_set > 0:
            self.num_days = manually_set
        if len(self.tasks) == 0:
            self.num_days = 10
        else:
            last_task = max(self.tasks, key=lambda x: self._utc_to_local(x["due_date"]))
            self.num_days = self._utc_to_local(last_task["due_date"]) - CURRENT_TIME
            if self.num_days.seconds > 0:
                self.num_days = self.num_days.days + 1
            else:
                self.num_days = self.num_days.days

    def build_time_slots(self):
        self.time_slots = {}
        for i in range(self.num_days):
            date = CURRENT_TIME.date() + datetime.timedelta(days=i)
            self.time_slots[date] = []
            for _ in range(UNITS_PER_DAY):
                self.time_slots[date].append((None, None))

    def get_message(self):
        if self.scheduler_success:
            return (False, "Success")
        else:
            return (True, "Not enough time to schedule tasks")

    def write_events_and_sleep(self):
        """Write User's Sleep Schedule and Events to Time Slots"""
        sleep_times = user_routes.get_sleep(self.user_id)
        wake_time, sleep_time = self._parse_sleep_time(
            sleep_times["startOfDay"], sleep_times["endOfDay"]
        )

        self.event_dict = self._parse_events()

        for i in range(self.num_days):
            date = CURRENT_TIME.date() + datetime.timedelta(days=i)
            self.time_slots[date][0 : int(wake_time)] = itertools.repeat(
                ("SLEEP", None), (int(wake_time))
            )
            self.time_slots[date][UNITS_PER_DAY - int(sleep_time) :] = itertools.repeat(
                ("SLEEP", None), (int(sleep_time))
            )

            if date in self.event_dict:
                for event in self.event_dict[date]:
                    start_units = event["start_units"]
                    end_units = event["end_units"]
                    self.time_slots[date][
                        int(start_units) : UNITS_PER_DAY - int(end_units)
                    ] = itertools.repeat(
                        ("EVENT", event.copy()),
                        (UNITS_PER_DAY - int(end_units) - int(start_units)),
                    )
                    # Write to first slot in day to indicate event or task has been written
                    self.time_slots[date][0] = ("NO_SKIP", None)

        # Write sleep until current time to prevent tasks being scheduled in the past
        today = CURRENT_TIME.date()
        cur_time_rounded = self._ceil_dt_fix(CURRENT_TIME)
        begin_day = (cur_time_rounded.hour * 60 + cur_time_rounded.minute) / TIME_UNIT

        for i in range(1, int(begin_day) + 1):
            if self.time_slots[today][i][0] != "EVENT":
                self.time_slots[today][i] = ("SLEEP", None)

    def schedule_tasks(self):
        """Auto Schedule Users Tasks in Time Slots"""
        for task in self.tasks:
            num_hours = float(task["estimated_time"])
            due_date = self._utc_to_local(task["due_date"])
            due_date_units, _ = self._dt_to_units(due_date)

            empty_slots = 0
            for i in range(self.num_days):
                date = CURRENT_TIME.date() + datetime.timedelta(days=i)
                day = self.time_slots[date]
                day_limit = UNITS_PER_DAY
                if date == due_date.date():
                    day_limit = due_date_units
                for j in range(int(day_limit)):
                    if day[j] == (None, None):
                        empty_slots += 1
            if (empty_slots / (60 / TIME_UNIT)) < num_hours:
                return False

        # List of Lists, Each Sublist has subtasks within
        # Sub tasks are Tuples of (Priority, Task Dictionary)
        pl_list = [[], [], [], [], [], []]
        sub_tasks_list = []
        for task in self.tasks:
            num_sub_tasks = (
                float(task["estimated_time"]) - float(task["completed_time"])
            ) / float(TIME_UNIT / 60)
            priority = self.generate_priority(
                task["estimated_time"],
                task["completed_time"],
                task["due_date"],
                self._ceil_dt(CURRENT_TIME, datetime.timedelta(minutes=30)),
            )
            for _ in range(int(num_sub_tasks)):
                sub_tasks_list.append((priority, task.copy()))

        empty_slot_count = 0
        for i in range(self.num_days):
            date = CURRENT_TIME.date() + datetime.timedelta(days=i)
            empty_slot_count += self.time_slots[date].count((None, None))

        if empty_slot_count < len(sub_tasks_list):
            return False

        sub_tasks_list.sort(key=lambda a: a[0], reverse=True)

        for item in sub_tasks_list:
            due_date = self._utc_to_local(item[1]["due_date"]).date()
            if due_date == CURRENT_TIME.date():
                pl_list[0].append(item)
            elif item[0] > 4:
                pl_list[1].append(item)
            elif item[0] > 2:
                pl_list[2].append(item)
            elif item[0] > 1:
                pl_list[3].append(item)
            elif item[0] > 0.25:
                pl_list[4].append(item)
            else:
                pl_list[5].append(item)

        while self._choose_pl_list(pl_list) != -1:
            for i in range(self.num_days):
                date = self._ceil_dt(
                    CURRENT_TIME, datetime.timedelta(minutes=30)
                ) + datetime.timedelta(days=i)
                day = self.time_slots[date.date()]
                written_task = ""
                for j in range(len(day)):
                    pl_index = self._choose_pl_list(pl_list)
                    if day[j] == (None, None):
                        if len(pl_list[pl_index]) > 0:
                            pop_idx = 0
                            if pl_index != 0:
                                if self._same_task_in_sub_list(pl_list[pl_index]):
                                    for idx, item in enumerate(pl_list[pl_index]):
                                        if item[1]["id"] == written_task:
                                            pop_idx = idx
                                            break
                            written_task = pl_list[pl_index].pop(pop_idx)
                            day[j] = ("TASK", written_task[1])
                            written_task = written_task[1]["id"]
                            self.time_slots[date.date()][0] = ("NO_SKIP", None)
                            pl_list = self.generate_priority_helper(
                                pl_list,
                                written_task,
                                date,
                            )

                            next_day = date + datetime.timedelta(days=1)
                            pl_list = self.split_and_sort_pl(pl_list, next_day)

        return True

    def split_and_sort_pl(self, pl_list_input, cur_day):
        for i, _ in enumerate(pl_list_input):
            pl_list_input[i].sort(key=lambda a: a[0], reverse=True)

        sub_tasks_list = []
        for _, sub_list in enumerate(pl_list_input):
            for _, val in enumerate(sub_list):
                sub_tasks_list.append(val)

        pl_list = [[], [], [], [], [], []]
        for item in sub_tasks_list:
            due_date = self._utc_to_local(item[1]["due_date"]).date()
            if due_date - cur_day.date() <= datetime.timedelta(0):
                pl_list[0].append(item)
            elif item[0] > 4:
                pl_list[1].append(item)
            elif item[0] > 2:
                pl_list[2].append(item)
            elif item[0] > 1:
                pl_list[3].append(item)
            elif item[0] > 0.25:
                pl_list[4].append(item)
            else:
                pl_list[5].append(item)

        return pl_list

    def generate_priority_helper(self, pl_list, written_task, cur_date):
        for sub_tasks_list in pl_list:
            for k in range(len(sub_tasks_list)):
                cur_sub_task = sub_tasks_list[k][1].copy()

                if cur_sub_task["id"] == written_task:
                    if "pending_time_done" in cur_sub_task:
                        cur_pending_time = cur_sub_task["pending_time_done"]
                        cur_sub_task.update(
                            {"pending_time_done": cur_pending_time + 0.5}
                        )
                    else:
                        cur_sub_task["pending_time_done"] = 0.5

                if "pending_time_done" in cur_sub_task:
                    priority = self.generate_priority(
                        cur_sub_task["estimated_time"],
                        cur_sub_task["completed_time"]
                        + cur_sub_task["pending_time_done"],
                        cur_sub_task["due_date"],
                        cur_date,
                    )
                else:
                    priority = self.generate_priority(
                        cur_sub_task["estimated_time"],
                        cur_sub_task["completed_time"],
                        cur_sub_task["due_date"],
                        cur_date,
                    )

                sub_tasks_list[k] = (
                    priority,
                    cur_sub_task,
                )
        return pl_list

    def generate_priority(
        self, estimated_time, completed_time, deadline, cur_day
    ) -> float:
        """Generate task's priority"""

        days = ((self._utc_to_local(deadline) - cur_day).total_seconds()) / 86400
        priority = (float(estimated_time) - float(completed_time)) / (float(days))
        return priority

    def define_blocks(self):
        """Define blocks to to be commited to DB"""
        db_batch = database.batch()
        for i in range(self.num_days):
            date = CURRENT_TIME.date() + datetime.timedelta(days=i)
            day = self.time_slots[date]

            if day[0][0] == "NO_SKIP":
                for index, slot in enumerate(day):
                    if slot[0] == "TASK":
                        block = Block().structure()
                        block["user_ids"] = [self.user_id]
                        block["type"] = "TASK"
                        block["task_id"] = slot[1]["id"]
                        block["name"] = slot[1]["name"]

                        start_time = self.index_to_dt(index, date)
                        block["start_time"] = start_time
                        block["end_time"] = start_time + datetime.timedelta(
                            minutes=TIME_UNIT
                        )
                        self._batch_create_blocks(db_batch, block)
                    else:
                        continue

        for date, event_list in self.event_dict.items():
            for event in event_list:
                block = Block().structure()
                block["user_ids"] = [self.user_id]
                if "collab" in event:
                    block["type"] = "COLLAB"
                else:
                    block["type"] = "EVENT"
                block["name"] = event["name"]
                block["start_time"] = event["start_time"]
                block["end_time"] = event["end_time"]
                self._batch_create_blocks(db_batch, block)

        for task in self.cram_tasks:
            block = Block().structure()
            block["user_ids"] = [self.user_id]
            block["task_id"] = task["id"]
            block["type"] = "CRAM"
            block["name"] = task["name"]
            block["start_time"] = self._ceil_dt(
                CURRENT_TIME, datetime.timedelta(minutes=30)
            )
            block["end_time"] = self._utc_to_local(task["due_date"])
            self._batch_create_blocks(db_batch, block)

        if self.batch_writes > 0:
            db_batch.commit()
            self.batch_writes = 0

    def _batch_create_blocks(self, db_batch, block_data):
        new_block_ref = database.collection("blocks").document()
        block_data["id"] = new_block_ref.id
        db_batch.set(new_block_ref, block_data)
        self.batch_writes += 1

        if self.batch_writes >= 400:
            db_batch.commit()
            self.batch_writes = 0

    def _parse_events(self):
        """Turn list of events into date keyed dictionary"""
        event_list, repeat_event_list = events_routes.get_events_scheduler(
            self.user_id, CURRENT_TIME.date()
        )
        event_list = [value for value in event_list.values()]

        repeat_event_list = [value for value in repeat_event_list.values()]

        event_dict = {}
        for event in event_list:
            start_time = self._utc_to_local(event["start_time"])
            end_time = self._utc_to_local(event["end_time"])
            start_units, end_units = self._dt_to_units(
                self._floor_dt_fix(start_time), self._ceil_dt_fix(end_time)
            )
            event["start_units"] = start_units
            event["end_units"] = end_units

            date = self._utc_to_local(event["start_time"]).date()
            if date not in event_dict:
                event_dict[date] = [event]
            else:
                event_dict[date].append(event)

        for event in repeat_event_list:
            start_time = self._utc_to_local(event["start_time"])
            end_time = self._utc_to_local(event["end_time"])
            start_units, end_units = self._dt_to_units(
                self._floor_dt_fix(start_time), self._ceil_dt_fix(end_time)
            )
            event["start_units"] = start_units
            event["end_units"] = end_units

            repeat_days = self._repeat_events_parser(event["repeat"])

            for i in range(-30, 31):
                date = CURRENT_TIME.date() + datetime.timedelta(days=i)
                if repeat_days == "MONTHLY" and date.day == start_time.date().day:
                    event["start_time"] = start_time.replace(
                        day=date.day, month=date.month, year=date.year
                    )
                    event["end_time"] = end_time.replace(
                        day=date.day, month=date.month, year=date.year
                    )
                    if date not in event_dict:
                        event_dict[date] = [event.copy()]
                    else:
                        event_dict[date].append(event.copy())
                elif repeat_days[date.weekday()]:
                    event["start_time"] = start_time.replace(
                        day=date.day, month=date.month, year=date.year
                    )
                    event["end_time"] = end_time.replace(
                        day=date.day, month=date.month, year=date.year
                    )
                    if date not in event_dict:
                        event_dict[date] = [event.copy()]
                    else:
                        event_dict[date].append(event.copy())

        return event_dict

    def _parse_sleep_time(self, start_time, end_time):
        """Parse sleep time into time units"""
        start_time = self._utc_to_local(start_time)

        end_time = self._utc_to_local(end_time)

        start_units, end_units = self._dt_to_units(start_time, end_time)

        return start_units, end_units

    def _round_time(self, cur_time, round_up):
        """Round time to nearest 30"""
        if round_up:
            if 0 <= cur_time.minute <= 30:
                cur_time = cur_time.replace(minute=30)
            else:
                cur_time = cur_time + datetime.timedelta(hours=1)
                cur_time = cur_time.replace(minute=0)
        else:
            if 0 <= cur_time.minute <= 30:
                cur_time = cur_time.replace(minute=0)
            else:
                cur_time = cur_time.replace(minute=30)

        return cur_time

    def _dt_to_units(self, start_time, end_time=CURRENT_TIME):
        """Convert datetime to time units"""
        start_units = (start_time.hour * 60 + start_time.minute) / TIME_UNIT
        end_delta = (end_time + datetime.timedelta(days=1)).replace(
            hour=0, minute=0
        ) - end_time
        end_units = int(end_delta.total_seconds() / 60) / TIME_UNIT

        return start_units, end_units

    def _utc_to_local(self, utc_string):
        utc_dt = parser.parse(utc_string)
        return utc_dt.replace(tzinfo=pytz.utc).astimezone(TIME_ZONE)

    def index_to_dt(self, index, date):
        time_delta = datetime.timedelta(minutes=index * TIME_UNIT)
        date_time = datetime.datetime(year=date.year, month=date.month, day=date.day)

        return (date_time + time_delta).astimezone(pytz.utc)

    def _ceil_dt(self, d_t, delta):
        return d_t + (datetime.datetime.min.replace(tzinfo=TIME_ZONE) - d_t) % delta

    def _ceil_dt_fix(self, d_t):
        if d_t.minute < 30:
            return d_t + datetime.timedelta(minutes=(30 - d_t.minute))
        elif d_t.minute > 30:
            return d_t + datetime.timedelta(minutes=(60 - d_t.minute))

        return d_t

    def _floor_dt_fix(self, d_t):
        if d_t.minute < 30:
            return d_t - datetime.timedelta(minutes=(d_t.minute))
        elif d_t.minute > 30:
            return d_t - datetime.timedelta(minutes=(30 - d_t.minute))

        return d_t

    def _choose_pl_list(self, pl_list):
        empty_list_count = 0
        for i in range(len(pl_list)):
            if len(pl_list[i]) == 0:
                empty_list_count += 1
            else:
                return i

        return -1

    def _same_task_in_sub_list(self, cur_list):
        cur_list = [item[1] for item in cur_list]

        cur_id = cur_list[0]["id"]

        for item in cur_list:
            if item["id"] != cur_id:
                return False

        return True

    def _repeat_events_parser(self, repeat_str):
        if repeat_str == "MONTHLY":
            return repeat_str

        repeat_days = {
            0: False,
            1: False,
            2: False,
            3: False,
            4: False,
            5: False,
            6: False,
        }
        day_parser = {"M": 0, "T": 1, "W": 2, "R": 3, "F": 4, "S": 5, "U": 6}

        for char in repeat_str:
            day_num = day_parser[char]
            if day_num in repeat_days:
                repeat_days[day_num] = True
        return repeat_days
        # M = Monday
        # T = Tuesday
        # W = Wednesday
        # R = Thursday
        # F = Friday
        # S = Saturday
        # U = Sunday
