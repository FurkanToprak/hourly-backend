""" Routes for blocks """
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


def get_block(params):
    """Get blocks"""
    result = (
        database.collection("blocks")
        .where("user_ids", "array_contains", params["id"])
        .get()
    )
    send = {}
    if result:
        for i, item in enumerate(result):
            send[i] = item.to_dict()
    return send


def delete_blocks(user_id):
    """Delete all blocks for a user"""
    result = (
        database.collection("blocks").where("user_ids", "array_contains", user_id).get()
    )

    db_batch = database.batch()
    for item in result:
        db_batch.delete(item.reference)

    db_batch.commit()
