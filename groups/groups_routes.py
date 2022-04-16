"""Routes for Groups"""
from datetime import datetime, timedelta
from google.cloud import firestore
from dateutil.parser import parse
from db_connection import database
from users.user_routes import get_names
from groups.models import Group
from groups.collaborators import Collab
from constants import COMPLETED


def create_group(params):
    """Create the event"""
    event_doc = database.collection("groups").document()
    group_id = event_doc.id
    group_struct = Group().structure()

    group_struct["id"] = group_id
    group_struct["user_ids"] = [params["user_id"]]
    group_struct["name"] = params["name"]
    group_struct["description"] = params["description"]
    group_struct["friends"][params["user_id"]] = []

    database.collection("groups").add(group_struct, group_id)
    return {"success": True}


def get_group_info(group_id):
    """Returns group information"""
    group_dict = database.collection("groups").document(group_id).get().to_dict()
    return {"group": group_dict}


def join_group(user_id, group_id):
    """Add user to group"""
    group_ref = database.collection("groups").document(group_id)

    if group_ref.get().exists:
        group_ref.update({"user_ids": firestore.ArrayUnion([user_id])})

        friends = group_ref.get().to_dict()["friends"]
        friends[user_id] = []
        group_ref.set({"friends": friends}, merge=True)

        return {"success": True}
    else:
        return {"success": False}


def leave_group(user_id, group_id):
    """Remove user from group"""
    group_ref = database.collection("groups").document(group_id)

    if group_ref.get().exists:
        group_ref.update({"user_ids": firestore.ArrayRemove([user_id])})

        friends = group_ref.get().to_dict()["friends"]
        friends.pop(user_id, None)

        for user, f_list in friends.items():
            if user_id in f_list:
                f_list.remove(user_id)
                friends[user] = f_list

        group_ref.set({"friends": friends}, merge=True)

        return {"success": True}

    return {"success": False}


def get_friends_list(group_id, user_id):
    """Get a user's friends list"""
    group_dict = database.collection("groups").document(group_id).get().to_dict()
    friends = group_dict["friends"]

    friend_dict = {
        "mutual": [],
        "awaiting_your_response": [],
        "awaiting_their_response": [],
        "no_relation": [],
    }

    if user_id not in friends:
        friends[user_id] = []

    for user in friends[user_id]:
        if user in friends:
            if user_id in friends[user]:
                friend_dict["mutual"].append(user)
            else:
                friend_dict["awaiting_their_response"].append(user)

    for user, f_list in friends.items():
        if user != user_id:
            if user_id in f_list:
                if user not in friend_dict["mutual"]:
                    friend_dict["awaiting_your_response"].append(user)
            elif user not in friend_dict["awaiting_their_response"]:
                friend_dict["no_relation"].append(user)

    for name, users in friend_dict.items():
        if users:
            friend_dict[name] = get_names(users)

    return friend_dict


def add_to_friends_list(group_id, user_id_1, user_id_2):
    """Add to a user's friends list"""
    group_dict = database.collection("groups").document(group_id).get().to_dict()

    friends = group_dict["friends"]

    if user_id_1 in friends:
        friends[user_id_1].append(user_id_2)
    else:
        friends[user_id_1] = [user_id_2]

    database.collection("groups").document(group_id).set(
        {"friends": friends}, merge=True
    )
    return {"success": True}


def remove_from_friends_list(group_id, user_id_1, user_id_2):
    """Remove from a user's friends list"""
    group_dict = database.collection("groups").document(group_id).get().to_dict()

    friends = group_dict["friends"]

    if user_id_1 in friends:
        if user_id_2 in friends[user_id_1]:
            friends[user_id_1].remove(user_id_2)
    if user_id_2 in friends:
        if user_id_1 in friends[user_id_2]:
            friends[user_id_2].remove(user_id_1)

    database.collection("groups").document(group_id).set(
        {"friends": friends}, merge=True
    )
    return {"success": True}


def check_collaborators(group_id, user_id_1, user_id_2, name_1, name_2, mail):
    """Check if two users can collaborate. If so, make events"""
    collab = Collab(
        user_id_1=user_id_1,
        user_id_2=user_id_2,
        name_1=name_1,
        name_2=name_2,
        mail=mail,
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
    for grp in groups:
        labels.append(grp["name"])

    return {"labels": labels}


def calculate_stats(group_id):
    """Calculate group statistics"""
    today = datetime.today().date()
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)

    group_tasks = get_group_tasks(group_id, start_day=monday)["group_tasks"]

    # Average hours estimated for group's tasks
    estimated_hours = []
    # Actual hours list
    completed_hours = []
    # Percent Complete vs Incomplete
    comp_task_count = 0
    incomp_task_count = 0
    # Total hours allocated for this week
    week_hours = 0
    for task in group_tasks:
        task_hours = float(task["estimated_time"])
        estimated_hours.append(task_hours)
        completed = float(task["completed_time"])
        completed_hours.append(completed)

        if parse(task["due_date"]).date() <= sunday:
            week_hours += task_hours

        if task["completed"] == COMPLETED:
            comp_task_count += 1
        else:
            incomp_task_count += 1

    return {
        "num_completed_tasks": comp_task_count,
        "num_incompleted_tasks": incomp_task_count,
        "estimated_hours_list": estimated_hours,
        "completed_hours_list": completed_hours,
        "total_week_hours": week_hours,
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
