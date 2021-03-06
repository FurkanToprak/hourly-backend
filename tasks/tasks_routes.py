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


def get_tasks(user_id):
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
    result = database.collection("tasks").document(task_id)

    if result:
        result.update({"do_not_schedule": True})
    else:
        return {"success": False}

    return {"success": True}


def get_task_scheduler(user_id):
    """Get all tasks for a user for the scheduler"""
    result = database.collection("tasks").where("user_id", "==", user_id).get()
    send = {}
    if result:
        for i, item in enumerate(result):
            temp = item.to_dict()
            if int(temp["completed"]) == NOT_COMPLETED:
                send[i] = temp
    return send


def update_task_hours(params):
    """Update a task's completed hours"""
    task_id = params["task_id"]
    hours = float(params["hours"])

    task = get_task_by_id(task_id)

    if float(task["estimated_time"]) == (float(task["completed_time"]) + hours):
        status = completed_task(task_id)
        if status is False:
            return {"success": False}

    database.collection("tasks").document(task_id).update(
        {"completed_time": (float(task["completed_time"]) + hours)}
    )
    return {"success": True}


def completed_task(task_id):
    """Set the task with the given task id to complete"""
    task_status = int(
        database.collection("tasks").document(task_id).get().to_dict()["completed"]
    )
    if task_status == COMPLETED:
        return False

    database.collection("tasks").document(task_id).update({"completed": COMPLETED})

    # Delete Task's Blocks
    result = database.collection("blocks").where("task_id", "==", task_id).get()
    db_batch = database.batch()
    for item in result:
        db_batch.delete(item.reference)
    db_batch.commit()

    return True
