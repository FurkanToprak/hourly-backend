""" Routes for items """
from items.models import Item
from db_connection import database
from constants import NOT_COMPLETED
from datetime import date


def createItem(params):
    """Create the item"""
    item_doc = database.collection("items").document()
    item_id = item_doc.id
    item = Item().structure()

    item["id"] = item_id
    item["user_id"] = params["user_id"]
    item["name"] = params["name"]
    item["start_date"] = date.today()
    item["due_date"] = params["due_date"]
    item["work_hours"] = params["user_id"]
    item["completed"] = NOT_COMPLETED

    database.collection("items").add(item, item_id)
    return "Item Created"
