""" Routes for events """
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
    event["date"] = params["date"]
    event["repeat"] = params["repeat"]

    database.collection("events").add(event, event_id)
    return "Event Created"


def get_events(params):
    """Get events"""
    result = database.collection("events").where("user_id", "==", params["id"]).get()
    send = {}
    if result:
        for i, item in enumerate(result):
            send[i] = item.to_dict()
    return send
