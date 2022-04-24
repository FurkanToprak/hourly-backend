"""Determine collaborator compatibility"""
import datetime
import os
import pytz
from scheduling.schedule import Schedule
from events.events_routes import create_event
from users.user_routes import get_email, update_refresh_schedule
from constants import STRF


CURRENT_TIME = (
    datetime.datetime.now(datetime.timezone.utc)
    .replace(tzinfo=pytz.utc)
    .astimezone(pytz.timezone("America/Chicago"))
)


class Collab:
    """Helper class for collaboration"""

    def __init__(self, user_id_1, user_id_2, name_1, name_2, mail) -> None:
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
        self.mail = mail

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

            for j in range(len(day_user_1) // 2), len(day_user_1):
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

            for j in range(len(day_user_1) // 2, len(day_user_1) - 1):
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
            "collab": "true",
        }
        create_event(params=params_1)

        params_2 = {
            "user_id": self.user_id_2,
            "name": f"Collaboration with {self.name_1}",
            "start_time": self.start_time.strftime(STRF),
            "end_time": self.end_time.strftime(STRF),
            "repeat": "",
            "collab": "true",
        }
        create_event(params=params_2)
        update_refresh_schedule(user_id=self.user_id_2, refresh=True)

    def send_emails(self):
        """Send users emails with contact information"""
        email_1 = get_email(self.user_id_1)
        email_2 = get_email(self.user_id_2)

        time = self.start_time.strftime("%B %-d, %Y at %-I:%M %p")
        try:
            self.mail.send_message(
                "h/ourly - Collaborator Found!",
                sender=os.environ["MAIL_USERNAME"],
                recipients=[email_1],
                body=f"We found you a collaborator!\n \
                       Collaborator's Name: {self.name_2}\n \
                       Collaborator's Email: {email_2}\n \
                       Meeting Time: {time}\n\n \
                       Be sure to send your collaborator an email and finalize your meeting!",
            )
        except Exception:
            print("Mail 1 Failed to Send")

        try:
            self.mail.send_message(
                "h/ourly - Collaborator Found!",
                sender=os.environ["MAIL_USERNAME"],
                recipients=[email_2],
                body=f"We found you a collaborator!\n \
                       Collaborator's Name: {self.name_1}\n \
                       Collaborator's Email: {email_1}\n \
                       Meeting Time: {time}\n\n \
                       Be sure to send your collaborator an email and finalize your meeting!",
            )
        except Exception:
            print("Mail 2 Failed to Send")

        return True
