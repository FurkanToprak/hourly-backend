""" Routes for blocks """
import itertools
from timeit import default_timer as timer
from datetime import datetime, timezone
from dateutil import parser
import pytz
from tasks.tasks_routes import get_task_by_id, delete_task
from blocks.models import Block
from db_connection import database


def create_block(params):
    """Create the blocks"""
    blocks_doc = database.collection("blocks").document()
    blocks_id = blocks_doc.id
    block = Block().structure()

    block["id"] = blocks_id
    block["user_ids"] = [params["user_id"]]
    block["task_id"] = params["task_id"]
    block["type"] = params["type"]
    block["name"] = params["name"]
    block["start_time"] = params["start_time"]
    block["end_time"] = params["end_time"]

    database.collection("blocks").add(block, blocks_id)
    return {"success": True}


def get_block_by_id(block_id):
    """Got block with the block id"""
    print(block_id)
    result = database.collection("blocks").where("id", "==", block_id).get()
    if result:
        return result[0].to_dict()
    return False


def get_blocks(user_id):
    """Get blocks for a given user via the user id"""
    result = (
        database.collection("blocks").where("user_ids", "array_contains", user_id).get()
    )
    send = []
    if result:
        for _i, item in enumerate(result):
            send.append(item.to_dict())

    start_time = timer()
    send = _merge_blocks(send)
    print(f"Merge Time - {timer() - start_time :0f}")

    send = _merge_blocks(send)

    return {"blocks": send}


def delete_blocks(user_id):
    """Delete all blocks for a user"""
    result = (
        database.collection("blocks").where("user_ids", "array_contains", user_id).get()
    )

    db_batch = database.batch()
    for item in result:
        db_batch.delete(item.reference)
    db_batch.commit()


def expired_sub_tasks(user_id):
    """Get all blocks that are expired"""
    blocks = get_blocks(user_id=user_id)["blocks"]
    cur_time = (
        datetime.now(timezone.utc)
        .replace(tzinfo=pytz.utc)
        .astimezone(pytz.timezone("America/Chicago"))
    )

    expired_tasks = []
    task_dict = {}
    for block in blocks:
        if block["type"] == "TASK":
            end_time = block["end_time"].astimezone(pytz.timezone("America/Chicago"))
            if end_time < cur_time:
                print("End Time Less")
                task_id = block["task_id"]

                if task_id in task_dict:
                    task_dict[task_id] += float(block["hours"])
                else:
                    task_dict[task_id] = float(block["hours"])

    for task_id, hours in task_dict.items():
        task = get_task_by_id(task_id)
        if task:
            task["hours"] = hours
            expired_tasks.append(task)

    expired_task_list = [
        task for task in expired_tasks if utc_to_local(task["due_date"]) >= cur_time
    ]
    past_due_tasks = [
        task for task in expired_tasks if utc_to_local(task["due_date"]) < cur_time
    ]

    id_list = []
    for task in past_due_tasks:
        id_list.append(task["id"])
    if id_list:
        result = database.collection("tasks").where("id", "in", id_list).get()
        db_batch = database.batch()
        for item in result:
            db_batch.delete(item.reference)
        db_batch.commit()

    return {"expired_tasks": expired_task_list, "past_due_tasks": past_due_tasks}


def _merge_blocks(block_list):
    task_list = []
    event_list = []
    for block in block_list:
        if block["type"] == "TASK":
            task_list.append(block)
        else:
            event_list.append(block)

    task_list = sorted(task_list, key=lambda d: d["start_time"])
    key_func = lambda x: x["task_id"]

    merged_tasks = []
    for _, group in itertools.groupby(task_list, key_func):
        group_list = list(group)

        i = 0
        while i < len(group_list) - 1:
            if group_list[i]["end_time"] == group_list[i + 1]["start_time"]:
                group_list[i]["end_time"] = group_list[i + 1]["end_time"]

                if "hours" in group_list[i]:
                    group_list[i]["hours"] += 0.5
                else:
                    group_list[i]["hours"] = 1

                group_list.pop(i + 1)
            else:
                i += 1
        merged_tasks.extend(group_list)

    for i, _ in enumerate(merged_tasks):
        if "hours" not in merged_tasks[i]:
            merged_tasks[i]["hours"] = 0.5

    return event_list + merged_tasks


def utc_to_local(utc_string):
    """Convert UTC to Local Time"""
    utc_dt = parser.parse(utc_string)
    return utc_dt.replace(tzinfo=pytz.utc).astimezone(pytz.timezone("America/Chicago"))


def get_cur_time():
    return (
        datetime.now(timezone.utc)
        .replace(tzinfo=pytz.utc)
        .astimezone(pytz.timezone("America/Chicago"))
    )
