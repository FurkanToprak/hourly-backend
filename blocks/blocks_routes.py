""" Routes for blocks """
import itertools
from timeit import default_timer as timer
from datetime import datetime
from dateutil import parser
import pytz
from blocks.models import Block
from db_connection import database
from constants import NOT_COMPLETED


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
    block["completed"] = NOT_COMPLETED

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
    blocks = get_blocks(user_id=user_id)["blocks"]
    cur_time = (
        datetime.datetime.now(datetime.timezone.utc)
        .replace(tzinfo=pytz.utc)
        .astimezone("America/Chicago")
    )

    expired_tasks = []
    for block in blocks:
        end_time = block["end_time"].astimezone(pytz.timezone("America/Chicago"))
        if block["type"] == "TASK" and end_time < cur_time:
            expired_tasks.append(block)

    return {"success": True}


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

                if "merge_count" in group_list[i]:
                    group_list[i]["merge_count"] += 1
                else:
                    group_list[i]["merge_count"] = 1

                group_list.pop(i + 1)
            else:
                i += 1
        merged_tasks.extend(group_list)

    for i, _ in enumerate(merged_tasks):
        if "merge_count" not in merged_tasks[i]:
            merged_tasks[i]["merge_count"] = 0

    return event_list + merged_tasks


def utc_to_local(utc_string):
    utc_dt = parser.parse(utc_string)
    return utc_dt.replace(tzinfo=pytz.utc).astimezone(pytz.timezone("America/Chicago"))
