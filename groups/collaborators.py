"""Determine collaborator compatibility"""
import datetime
import pytz
from scheduling.schedule import Schedule
from events.events_routes import create_event


CURRENT_TIME = (
    datetime.datetime.now(datetime.timezone.utc)
    .replace(tzinfo=pytz.utc)
    .astimezone(pytz.timezone("America/Chicago"))
)

STRF = "%Y-%m-%dT%H:%M:%SZ"


class Collab:
    """Helper class for collaboration"""

    def __init__(self, user_id_1, user_id_2, name_1, name_2) -> None:
        self.user_id_1 = user_id_1
        self.user_id_2 = user_id_2
        self.name_1 = name_1
        self.name_2 = name_2
        self.scheduler_1 = Schedule(self.user_id_1)
        self.scheduler_2 = Schedule(self.user_id_2)
        self.time_slots_1 = None
        self.time_slots_2 = None
        self.start_time = None
        self.end_time = None

    def run(self) -> bool:
        """Class Runner"""
        self.get_time_slots()
        if self.find_meeting_time():
            self.make_event()
            self.send_emails()
            return True

        return False

    def get_time_slots(self):
        """Fill time slots in scheduler"""
        self.scheduler_1.set_num_days(manually_set=7)
        self.scheduler_2.set_num_days(manually_set=7)

        self.scheduler_1.build_time_slots()
        self.scheduler_2.build_time_slots()

        self.scheduler_1.write_events_and_sleep()
        self.scheduler_2.write_events_and_sleep()

        self.time_slots_1 = self.scheduler_1.time_slots
        self.time_slots_2 = self.scheduler_2.time_slots

    def mark_morning(self):
        """Mark morning slots to prevent scheduling"""
        for i in range(7):
            date = CURRENT_TIME.date() + datetime.timedelta(days=i)

            day_user_1 = self.time_slots_1[date]
            day_user_2 = self.time_slots_2[date]

            for j in range(len(day_user_1) // 2):
                if day_user_1[j] == (None, None):
                    day_user_1[j] = ("SLEEP", None)
                if day_user_2[j] == (None, None):
                    day_user_2[j] = ("SLEEP", None)

    def find_meeting_time(self):
        """Find empty time slot for both users"""
        for i in range(7):
            date = CURRENT_TIME.date() + datetime.timedelta(days=i)

            day_user_1 = self.time_slots_1[date]
            day_user_2 = self.time_slots_2[date]

            for j in range(len(day_user_1) - 1):
                if day_user_1[j] == (None, None) and day_user_2[j] == (None, None):
                    if day_user_1[j + 1] == (None, None) and day_user_2[j + 1] == (
                        None,
                        None,
                    ):
                        self.start_time = self.scheduler_1.index_to_dt(j, date)
                        self.end_time = self.start_time + datetime.timedelta(hours=1)
                        return True

        return False

    def make_event(self):
        """Create events for users"""
        params_1 = {
            "user_id": self.user_id_1,
            "name": f"Collaboration with {self.name_2}",
            "start_time": self.start_time.strftime(STRF),
            "end_time": self.end_time.strftime(STRF),
            "repeat": "",
        }
        create_event(params=params_1)

        params_2 = {
            "user_id": self.user_id_2,
            "name": f"Collaboration with {self.name_1}",
            "start_time": self.start_time.strftime(STRF),
            "end_time": self.end_time.strftime(STRF),
            "repeat": "",
        }
        create_event(params=params_2)

    def send_emails(self):
        """Send users emails with contact information"""
        return True
