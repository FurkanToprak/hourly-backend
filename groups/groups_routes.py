"""Routes for Groups"""
from datetime import datetime, timedelta
from statistics import mean
from dateutil.parser import parse
from db_connection import database
from groups.models import Group
from constants import COMPLETED, NOT_COMPLETED


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

    average_hours = mean(estimated_hours)

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
    user_ids = database.collection("groups").document(group_id).get().to_dict()
    user_ids = user_ids["user_ids"]

    result = database.collection("tasks").where("user_id", "in", user_ids).get()

    send = []
    if result:
        for _, item in enumerate(result):
            if parse(item.to_dict()["due_date"]).date() >= start_day:
                send.append(item.to_dict())

    return {"group_tasks": send}
