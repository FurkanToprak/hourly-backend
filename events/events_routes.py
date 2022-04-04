""" Routes for events """
from datetime import datetime, timedelta
from dateutil import parser
import pytz
from events.models import Event
from db_connection import database


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
