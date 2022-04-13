""" Routes for events """
from datetime import datetime, timedelta, date
from timeit import default_timer as timer
from dateutil import parser
import pytz
from icalendar import Calendar
from events.models import Event
from db_connection import database
from constants import STRF


def create_event(params):
    """Create the event"""
    event_doc = database.collection("events").document()
    event_id = event_doc.id
    event = Event().structure()

    event["id"] = event_id
    event["user_id"] = params["user_id"]
    event["name"] = params["name"]
    event["start_time"] = params["start_time"]
    event["end_time"] = params["end_time"]
    event["repeat"] = params["repeat"]

    database.collection("events").add(event, event_id)
    return {"success": True}


def get_events(user_id):
    """Get all of a users events"""
    non_repeat_events, repeat_events = get_current_events(
        user_id=user_id, cur_date=datetime.today().date()
    )

    non_repeat_send = []
    if non_repeat_events:
        for _, item in enumerate(non_repeat_events):
            non_repeat_send.append(item.to_dict())

    repeat_send = []
    if repeat_events:
        for _, item in enumerate(repeat_events):
            repeat_send.append(item.to_dict())

    return {"events": (non_repeat_send + repeat_send)}


def delete_event(event_id):
    """Delete an event"""
    result = database.collection("events").where("id", "==", event_id).get()
    if result:
        for item in result:
            item.reference.delete()
        return {"success": True}

    return {"success": False}


def parse_ics_file(ics_file, user_id, start_point):
    """Parse an ICS into events"""
    gcal = Calendar.from_ical(ics_file.read())
    db_batch = database.batch()

    event_params = {
        "user_id": user_id,
        "name": "",
        "start_time": "",
        "end_time": "",
        "repeat": "",
    }
    start_point = utc_to_local(start_point)
    for component in gcal.walk():
        if component.name == "VEVENT":
            if type(component.get("dtstart").dt) is date:
                continue
            event_params["name"] = component.get("summary")
            event_params["start_time"] = (
                component.get("dtstart").dt.replace(
                    tzinfo=pytz.timezone("America/Chicago")
                )
                + timedelta(hours=5)
            ).strftime(STRF)
            if event_params["start_time"] < start_point:
                continue
            event_params["end_time"] = (
                component.get("dtend").dt.replace(
                    tzinfo=pytz.timezone("America/Chicago")
                )
                + timedelta(hours=5)
            ).strftime(STRF)
            rrule = component.get("rrule")
            if rrule:
                if "UNTIL" in rrule:
                    if rrule["UNTIL"][0].date() < datetime.now().date():
                        continue
                repeat = ""
                if "DAILY" in rrule["FREQ"]:
                    repeat = "MTWRFSU"
                elif "WEEKLY" in rrule["FREQ"]:
                    if "BYDAY" in rrule:
                        if "SU" in rrule["BYDAY"]:
                            repeat += "U"
                        if "MO" in rrule["BYDAY"]:
                            repeat += "M"
                        if "TU" in rrule["BYDAY"]:
                            repeat += "T"
                        if "WE" in rrule["BYDAY"]:
                            repeat += "W"
                        if "TH" in rrule["BYDAY"]:
                            repeat += "R"
                        if "FR" in rrule["BYDAY"]:
                            repeat += "F"
                        if "SA" in rrule["BYDAY"]:
                            repeat += "S"
                    else:
                        day_parser = {
                            0: "M",
                            1: "T",
                            2: "W",
                            3: "R",
                            4: "F",
                            5: "S",
                            6: "U",
                        }
                        day = component.get("dtstart").dt.weekday()
                        repeat = day_parser[day]

                elif "MONTHLY" in rrule["FREQ"]:
                    repeat = "MONTHLY"
                event_params["repeat"] = repeat

            batch_create_event(db_batch=db_batch, params=event_params)
            event_params["repeat"] = ""

    db_batch.commit()
    return {"success": True}


def batch_create_event(db_batch, params):
    """Create events via batch"""
    new_event_ref = database.collection("events").document()
    params["id"] = new_event_ref.id
    db_batch.set(new_event_ref, params)


def get_events_scheduler(user_id, cur_date):
    """Get events for scheduler"""
    non_repeat_events, repeat_events = get_current_events(user_id, cur_date)
    non_repeat_send = {}
    if non_repeat_events:
        for i, item in enumerate(non_repeat_events):
            non_repeat_send[i] = item.to_dict()

    repeat_send = {}
    if repeat_events:
        for i, item in enumerate(repeat_events):
            repeat_send[i] = item.to_dict()

    return non_repeat_send, repeat_send


def get_current_events(user_id, cur_date):
    """Get all repeating events and events >= current date"""
    repeat_events = (
        database.collection("events")
        .where("user_id", "==", user_id)
        .where("repeat", "!=", "")
        .get()
    )
    non_repeat_events = (
        database.collection("events")
        .where("user_id", "==", user_id)
        .where("repeat", "==", "")
        .get()
    )

    month_prior = cur_date - timedelta(days=30)
    month_later = cur_date + timedelta(days=30)

    non_repeat_events = [
        item
        for item in non_repeat_events
        if month_prior
        <= utc_to_local(item.to_dict()["start_time"]).date()
        <= month_later
    ]

    return non_repeat_events, repeat_events


def utc_to_local(utc_string):
    utc_dt = parser.parse(utc_string)
    return utc_dt.replace(tzinfo=pytz.utc).astimezone(pytz.timezone("America/Chicago"))
