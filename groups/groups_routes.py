"""Routes for Groups"""
from datetime import datetime, timedelta
from statistics import mean
from google.cloud import firestore
from dateutil.parser import parse
from db_connection import database
from groups.models import Group
from groups.collaborators import Collab
from constants import COMPLETED


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
    return {"success": True}


def join_group(user_id, group_id):
    """Add user to group"""
    group_ref = database.collection("groups").document(group_id)

    group_ref.update({"user_ids": firestore.ArrayUnion([user_id])})

    return {"success": True}


def leave_group(user_id, group_id):
    """Remove user from group"""
    group_ref = database.collection("groups").document(group_id)

    group_ref.update({"user_ids": firestore.ArrayRemove([user_id])})

    return {"success": True}


def get_collaborators(group_id):
    """Get all people looking for a collaborator"""
    group = database.collection("groups").document(group_id).get().to_dict()
    return {"collaborators": group["collaborators"]}


def place_collaborator(user_id, user_name, group_id):
    """Add user to collaborator list"""
    group_ref = database.collection("groups").document(group_id)

    group_ref.update(
        {
            "collaborators": firestore.ArrayUnion(
                [{"user_id": user_id, "user_name": user_name}]
            )
        }
    )

    return {"success": True}


def check_collaborators(group_id, user_id_1, user_id_2, name_1, name_2):
    """Check if two users can collaborate. If so, make events"""
    collab = Collab(
        user_id_1=user_id_1, user_id_2=user_id_2, name_1=name_1, name_2=name_2
    )

    if collab.run():
        group_ref = database.collection("groups").document(group_id)
        group_ref.update(
            {
                "collaborators": firestore.ArrayRemove(
                    [{"user_id": user_id_1, "user_name": name_1}]
                )
            }
        )
        start_time = collab.start_time
        end_time = collab.end_time
        return {
            "success": True,
            "start_time": start_time,
            "end_time": end_time,
            "name": name_2,
        }

    return {"success": False}


def get_users_groups(user_id):
    """Get all groups a user is in"""
    result = (
        database.collection("groups").where("user_ids", "array_contains", user_id).get()
    )

    send = []
    for item in result:
        send.append(item.to_dict())

    return {"groups": send}


def get_group_members(group_id):
    """Get all members of a group"""
    users = database.collection("groups").document(group_id).get().to_dict()["user_ids"]

    name_ref = database.collection("users").where("id", "in", users).get()

    names = []
    for item in name_ref:
        names.append(item.to_dict()["name"])

    return {"names": names}


def get_labels(user_id):
    """Get all group names for a user, for labels"""
    groups = get_users_groups(user_id=user_id)["groups"]

    labels = []
    for group in groups:
        labels.append(group["name"])

    return {"labels": labels}


def calculate_stats(group_id):
    """Calculate group statistics"""
    today = datetime.today().date()
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)

    group_tasks = get_group_tasks(group_id, start_day=monday)["group_tasks"]

    # Average hours estimated for group's tasks
    estimated_hours = []
    # Percent Complete vs Incomplete
    comp_task_count = 0
    incomp_task_count = 0
    # Total hours allocated for this week
    week_hours = 0
    # Complete Task Estimated vs Actual
    comp_task_estimated_hours = 0
    comp_task_actual_hours = 0
    for task in group_tasks:
        task_hours = float(task["estimated_time"])
        estimated_hours.append(task_hours)

        if parse(task["due_date"]).date() <= sunday:
            week_hours += task_hours

            if task["completed"] == COMPLETED:
                comp_task_estimated_hours += task_hours
                comp_task_actual_hours += float(task["completed_time"])

        if task["completed"] == COMPLETED:
            comp_task_count += 1
        else:
            incomp_task_count += 1
    if estimated_hours:
        average_hours = mean(estimated_hours)
    else:
        average_hours = 0

    return {
        "average_hours": average_hours,
        "num_completed_tasks": comp_task_count,
        "num_incompleted_tasks": incomp_task_count,
        "completed_task_estimated_hours": comp_task_estimated_hours,
        "completed_task_actual_hours": comp_task_actual_hours,
        "total_group_hours_for_week": week_hours,
    }


def get_group_tasks(group_id, start_day=datetime.today().date()):
    """Get all tasks for a group"""
    group = database.collection("groups").document(group_id).get().to_dict()
    group_name = group["name"]

    result = database.collection("tasks").where("label", "==", group_name).get()

    send = []
    if result:
        for _, item in enumerate(result):
            if parse(item.to_dict()["due_date"]).date() >= start_day:
                send.append(item.to_dict())

    return {"group_tasks": send}
