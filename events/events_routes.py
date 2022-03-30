""" Routes for events """
from events.models import Event
from db_connection import database
from dateutil import parser


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
    return "Event Created"


def get_events(user_id):
    """Get events"""
    result = database.collection("events").where("user_id", "==", user_id).get()
    send = []
    if result:
        for item in result:
            send.append(item.to_dict())
    return {"events": send}


def get_events_scheduler(user_id, cur_date):
    """Get events"""
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

    non_repeat_events = [
        item
        for item in non_repeat_events
        if parser.parse(item.to_dict()["start_time"]).date() >= cur_date
    ]
    non_repeat_send = {}
    if non_repeat_events:
        for i, item in enumerate(non_repeat_events):
            non_repeat_send[i] = item.to_dict()

    repeat_send = {}
    if repeat_events:
        for i, item in enumerate(repeat_events):
            repeat_send[i] = item.to_dict()

    return non_repeat_send, repeat_send
