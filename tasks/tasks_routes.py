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
    task["user_id"] = params["id"]
    task["name"] = params["name"]
    task["label"] = params["label"]
    task["description"] = params["description"]
    task["start_date"] = str(date.today())
    task["due_date"] = params["due_date"]
    task["estimated_time"] = params["estimated_time"]
    task["completed"] = NOT_COMPLETED

    database.collection("tasks").add(task, tasks_id)
    return task


def get_task(params):
    """Get a task"""
    print("look params")
    print(params)
    result = database.collection("tasks").where("user_id", "==", params["id"]).get()
    send = {}
    if result:
        for item in result:
            dict_item = item.to_dict()
            send[dict_item["id"]] = dict_item
    return send
