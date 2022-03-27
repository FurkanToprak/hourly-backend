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
from constants import NOT_COMPLETED
import pprint


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
        self.last_task = None
        self.num_days = 0
        self.batch_writes = 0
        self.return_message = "Success"
        self.scheduler()

    def scheduler(self):
        """Main scheduling flow"""
        self.tasks = tasks_routes.get_task_scheduler(self.user_id)
        self.tasks = [value for value in self.tasks.values()]
        self.last_task = max(
            self.tasks, key=lambda x: self._utc_to_local(x["due_date"])
        )
        # self.time_slots = (self.last_task - CURRENT_TIME).days * UNITS_PER_DAY * [None]
        self.num_days = self._utc_to_local(self.last_task["due_date"]) - CURRENT_TIME

        if self.num_days.seconds > 0:
            self.num_days = self.num_days.days + 1
        else:
            self.num_days = self.num_days.days

        self.time_slots = {}
        for i in range(self.num_days):
            date = CURRENT_TIME.date() + datetime.timedelta(days=i)
            self.time_slots[date] = []
            for _ in range(UNITS_PER_DAY):
                self.time_slots[date].append((None, None))

        print("Writing Events and Sleep")
        self.write_events_and_sleep()
        print("Scheduling Tasks")
        enough_time = self.schedule_tasks()

        if enough_time:
            # Delete old blocks
            delete_blocks(self.user_id)
            print("Defining Blocks")
            self.define_blocks()
            print("Done")
        else:
            self.return_message = "Not enough time to schedule tasks"

    def write_events_and_sleep(self):
        """Write User's Sleep Schedule and Events to Time Slots"""
        sleep_times = user_routes.get_sleep(self.user_id)
        wake_time, sleep_time = self._parse_sleep_time(
            sleep_times["startOfDay"], sleep_times["endOfDay"]
        )

        event_dict = self._parse_events()

        for i in range(self.num_days):
            date = CURRENT_TIME.date() + datetime.timedelta(days=i)
            self.time_slots[date][0 : int(wake_time)] = itertools.repeat(
                ("SLEEP", None), (int(wake_time))
            )
            self.time_slots[date][UNITS_PER_DAY - int(sleep_time) :] = itertools.repeat(
                ("SLEEP", None), (int(sleep_time))
            )

            if date in event_dict:
                for event in event_dict[date]:
                    start_units = event["start_units"]
                    end_units = event["end_units"]
                    self.time_slots[date][
                        int(start_units) : int(end_units)
                    ] = itertools.repeat(
                        ("EVENT", event.copy()), (int(end_units) - int(start_units))
                    )
                    # Write to first slot in day to indicate event or task has been written
                    self.time_slots[date][0] = ("NO_SKIP", None)

    def schedule_tasks(self):
        """Auto Schedule Users Tasks in Time Slots"""
        sub_tasks_list = []
        for task in self.tasks:
            num_sub_tasks = float(task["estimated_time"]) / 0.5
            priority = self.generate_priority(
                task["estimated_time"], task["completed_time"], task["due_date"]
            )
            for _ in range(int(num_sub_tasks)):
                sub_tasks_list.append((priority, task))

        empty_slot_count = 0
        for i in range(self.num_days):
            date = CURRENT_TIME.date() + datetime.timedelta(days=i)
            empty_slot_count += self.time_slots[date].count((None, None))

        if empty_slot_count < len(sub_tasks_list):
            return False

        sub_tasks_list.sort(key=lambda a: a[0])
        while len(sub_tasks_list) > 0:
            for i in range(self.num_days):
                date = CURRENT_TIME.date() + datetime.timedelta(days=i)
                day = self.time_slots[date]

                for j in range(len(day)):
                    if day[j] == (None, None):
                        if len(sub_tasks_list) > 0:
                            written_task = sub_tasks_list.pop()
                            day[j] = ("TASK", written_task)
                            self.time_slots[date][0] = ("NO_SKIP", None)

                            for k in range(len(sub_tasks_list)):
                                if sub_tasks_list[k][1] == written_task:
                                    if "pending_time_done" in sub_tasks_list[k][1]:
                                        sub_tasks_list[k][1]["pending_time_done"] += 1
                                    else:
                                        sub_tasks_list[k][1]["pending_time_done"] = 1

                                if "pending_time_done" in sub_tasks_list[k][1]:
                                    priority = self.generate_priority(
                                        sub_tasks_list[k][1]["estimated_time"],
                                        sub_tasks_list[k][1]["completed_time"]
                                        + sub_tasks_list[k][1]["pending_time_done"],
                                        sub_tasks_list[k][1]["due_date"],
                                    )
                                else:
                                    priority = self.generate_priority(
                                        sub_tasks_list[k][1]["estimated_time"],
                                        sub_tasks_list[k][1]["completed_time"],
                                        sub_tasks_list[k][1]["due_date"],
                                    )

                                sub_tasks_list[k] = (priority, sub_tasks_list[k][1])
        return True

    def generate_priority(self, estimated_time, completed_time, deadline) -> float:
        """Generate task's priority"""
        priority = (float(estimated_time) - float(completed_time)) / (
            (self._utc_to_local(deadline) - CURRENT_TIME).total_seconds() / 3600
        )
        return priority

    def define_blocks(self):
        """Define blocks to to be commited to DB"""
        db_batch = database.batch()
        for i in range(self.num_days):
            date = CURRENT_TIME.date() + datetime.timedelta(days=i)
            day = self.time_slots[date]

            if day[0][0] == "NO_SKIP":
                last_written_block = None
                for index, slot in enumerate(day):
                    if slot[0] == "EVENT":
                        if slot[1] != last_written_block:
                            block = Block().structure()
                            block["user_ids"] = [self.user_id]
                            block["type"] = "EVENT"
                            block["name"] = slot[1]["name"]
                            block["start_time"] = parser.parse(
                                slot[1]["start_time"]
                            ).astimezone(pytz.utc)
                            block["end_time"] = parser.parse(
                                slot[1]["end_time"]
                            ).astimezone(pytz.utc)
                            self._batch_create_blocks(db_batch, block)

                            last_written_block = slot[1]
                        else:
                            continue
                    elif slot[0] == "TASK":
                        block = Block().structure()
                        block["user_ids"] = [self.user_id]
                        block["type"] = "TASK"
                        block["task_id"] = slot[1][1]["id"]
                        block["name"] = slot[1][1]["name"]

                        start_time = self._index_to_dt(index, date)
                        block["start_time"] = start_time
                        block["end_time"] = start_time + datetime.timedelta(
                            minutes=TIME_UNIT
                        )
                        block["completed"] = NOT_COMPLETED
                        self._batch_create_blocks(db_batch, block)
                    else:
                        continue

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
        event_list = events_routes.get_events_scheduler(self.user_id)
        event_list = [value for value in event_list.values()]

        event_dict = {}
        for event in event_list:
            start_time = self._round_time(
                self._utc_to_local(event["start_time"]), False
            )
            end_time = self._round_time(self._utc_to_local(event["end_time"]), True)
            start_units, end_units = self._dt_to_units(start_time, end_time)
            event["start_units"] = start_units
            event["end_units"] = end_units

            date = self._utc_to_local(event["start_time"]).date()
            if date not in event_dict:
                event_dict[date] = [event]
            else:
                event_dict[date].append(event)

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

    def _dt_to_units(self, start_time, end_time):
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

    def _index_to_dt(self, index, date):
        time_delta = datetime.timedelta(minutes=index * TIME_UNIT)
        date_time = datetime.datetime(year=date.year, month=date.month, day=date.day)

        return (date_time + time_delta).astimezone(pytz.utc)

    def get_message(self):
        if self.return_message == "Success":
            return (False, self.return_message)
        else:
            return (True, self.return_message)
