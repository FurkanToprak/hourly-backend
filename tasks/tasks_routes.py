""" Routes for tasks """
from datetime import date
from tasks.models import Task
from db_connection import database
from constants import NOT_COMPLETED


def create_task(params):
    """Create the tasks"""
    tasks_doc = database.collection("tasks").document()
    tasks_id = tasks_doc.id
    task = Task().structure()

    task["id"] = tasks_id
    task["user_id"] = params["user_id"]
    task["name"] = params["name"]
    task["label"] = params["label"]
    task["description"] = params["description"]
    task["start_date"] = str(date.today())
    task["estimated_time"] = params["estimatedTime"]
    task["completed_time"] = 0
    task["due_date"] = params["due_date"]
    task["completed"] = NOT_COMPLETED

    database.collection("tasks").add(task, tasks_id)
    return task


def get_task(params):
    """Get all tasks for a user"""
    result = database.collection("tasks").where("user_id", "==", params["id"]).get()
    send = []
    if result:
        for item in result:
            send.append(item.to_dict())
    return {"tasks": send}


def get_task_by_id(params):
    """Get a task"""
    result = database.collection("tasks").where("id", "==", params["id"]).get()
    if result:
        return result[0].to_dict()
    else:
        return False


def get_task_scheduler(user_id):
    """Get all tasks for a user for the scheduler"""
    result = database.collection("tasks").where("user_id", "==", user_id).get()
    send = {}
    if result:
        for item in result:
            send[item.to_dict()["id"]] = item.to_dict()
    return send
