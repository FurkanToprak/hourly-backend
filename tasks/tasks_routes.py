""" Routes for tasks """
from datetime import date
from tasks.models import Task
from db_connection import database
from constants import NOT_COMPLETED, COMPLETED


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
    task["estimated_time"] = params["estimated_time"]
    task["completed_time"] = 0
    task["due_date"] = params["due_date"]
    task["completed"] = NOT_COMPLETED
    task["do_not_schedule"] = False

    database.collection("tasks").add(task, tasks_id)
    return task


def get_task(user_id):
    """Get all tasks for a user"""
    result = database.collection("tasks").where("user_id", "==", user_id).get()
    send = []
    if result:
        for item in result:
            send.append(item.to_dict())
    return {"tasks": send}


def get_task_by_id(task_id):
    """Get a task with task id"""
    result = database.collection("tasks").where("id", "==", task_id).get()
    if result:
        return result[0].to_dict()
    else:
        return False


def delete_task(task_id):
    """Delete a task"""
    result = database.collection("tasks").where("id", "==", task_id).get()
    if result:
        for item in result:
            item.reference.delete()
        return {"success": True}

    return {"success": False}


def cram_task(task_id):
    """Mark a task as do_not_schedule to indicate cram"""
    result = database.collection("tasks").where("id", "==", task_id).get()

    if result:
        result.update({"do_not_schedule": task_id})
    else:
        return {"success": False}

    return {"success": True}


def get_task_scheduler(user_id):
    """Get all tasks for a user for the scheduler"""
    result = database.collection("tasks").where("user_id", "==", user_id).get()
    send = {}
    if result:
        for item in result:
            send[item.to_dict()["id"]] = item.to_dict()
    return send


def update_task_hours(params):
    task_id = params["task_id"]
    hours = params["hours"]

    task = get_task_by_id(task_id)

    if task["estimated_time"] == (task["completed_time"] + hours):
        status = completed_task(task_id)
        if status is False:
            return {"succuess": False}

    database.collection("tasks").document(task_id).update(
        {"completed_time": (task["completed_time"] + hours)}
    )
    return {"success": True}


def completed_task(task_id):
    """Set the task with the given task id to complete"""
    task_status = database.collection("tasks").where("id", "==", task_id)["completed"]
    if task_status == COMPLETED:
        return False
    else:
        database.collection("tasks").document(task_id).update({"completed": COMPLETED})
        return True
