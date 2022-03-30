""" Routes for tasks """
from datetime import date
from tasks.models import Task
from db_connection import database
from constants import NOT_COMPLETED, COMPLETED
from blocks import blocks_routes


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


# TODO: Make Delete Task and Mark as Do Not Schedule


def get_task_scheduler(user_id):
    """Get all tasks for a user for the scheduler"""
    result = database.collection("tasks").where("user_id", "==", user_id).get()
    send = {}
    if result:
        for item in result:
            send[item.to_dict()["id"]] = item.to_dict()
    return send


def update_task_hours(params):
    block_ids = params["blocks"]
    blocks = []

    for block_id in block_ids:
        blocks.append(blocks_routes.get_block_by_id(block_id))

    for block in blocks:
        task_id = block["task_id"]
        task = get_task_by_id(task_id)

        if task["estimated_time"] == (task["completed_time"] + 0.5):
            status = completed_task(task_id)

            if status is False:
                continue

        database.collection("tasks").document(task_id).update(
            {"completed_time": (task["completed_time"] + 0.5)}
        )
    return "updated task"


def completed_task(task_id):
    """Set the task with the given task id to complete"""
    task_status = database.collection("tasks").where("id", "==", task_id)["completed"]
    if task_status == COMPLETED:
        return False
    else:
        database.collection("tasks").document(task_id).update({"completed": COMPLETED})
        return True
