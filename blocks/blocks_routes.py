""" Routes for blocks """
import itertools
from timeit import default_timer as timer
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
    return "Block Created"


def get_block(user_id):
    """Get blocks"""
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

    for i in range(len(merged_tasks)):
        if "merge_count" not in merged_tasks[i]:
            merged_tasks[i]["merge_count"] = 0

    return event_list + merged_tasks
