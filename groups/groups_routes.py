"""Routes for Groups"""
from db_connection import database
from groups.models import Group


def create_group(params):
    """Create the event"""
    event_doc = database.collection("groups").document()
    group_id = event_doc.id
    group = Group().structure()

    group["id"] = group_id
    group["user_ids"] = [params["user_id"]]
    group["name"] = params["name"]
    group["description"] = params["description"]

    database.collection("groups").add(group, group_id)
    return "Group Created"


def get_group_tasks(group_id):
    """Get all tasks for a group (for stats)"""
    user_ids = database.collection("groups").document(group_id).get().to_dict()
    user_ids = user_ids["user_ids"]

    result = database.collection("tasks").where("user_id", "in", user_ids).get()

    send = []
    if result:
        for _, item in enumerate(result):
            send.append(item.to_dict())

    return {"group_tasks": send}
