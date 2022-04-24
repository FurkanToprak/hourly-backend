"""Routes for Users"""
from flask import jsonify
from users.models import User
from db_connection import database


def login(email, name, start_day, end_day):
    """Check If user is logged in"""
    user = User().structure()
    result = database.collection("users").where("email", "==", email).get()
    if result:
        user_match = result[0].to_dict()
        refresh = False
        if user_match["refresh_schedule"]:
            refresh = True
            update_refresh_schedule(user_id=user_match["id"], refresh=False)

        send = {
            "id": user_match["id"],
            "startOfDay": user_match["startOfDay"],
            "endOfDay": user_match["endOfDay"],
            "refresh_schedule": refresh,
        }
    else:
        doc_ref = database.collection("users").document()
        doc_id = doc_ref.id

        user["id"] = doc_id
        user["email"] = email
        user["name"] = name
        user["startOfDay"] = start_day
        user["endOfDay"] = end_day
        user["refresh_schedule"] = False
        database.collection("users").add(user, doc_id)
        send = {"id": doc_id, "startOfDay": start_day, "endOfDay": end_day}
    return jsonify(send)


def get_sleep(user_id):
    """Return User's Sleep Time"""
    result = database.collection("users").where("id", "==", user_id).get()
    send = {}
    if result:
        send["startOfDay"] = result[0].to_dict()["startOfDay"]
        send["endOfDay"] = result[0].to_dict()["endOfDay"]

    return send


def update_sleep(user_id, start_day, end_day):
    """Return User's Sleep Time"""
    result = database.collection("users").document(user_id)
    if result.get().exists:
        result.update({"startOfDay": start_day, "endOfDay": end_day})
        return jsonify(success=True)

    return jsonify(success=False)


def get_names(user_list):
    """Return a list of user's names"""
    result = database.collection("users").where("id", "in", user_list).get()

    send = []
    for item in result:
        send.append((item.to_dict()["id"], item.to_dict()["name"]))

    return send


def get_email(user_id):
    """Return a list of user's names"""
    result = database.collection("users").where("id", "==", user_id).get()

    email = ""
    for item in result:
        email = item.to_dict()["email"]

    return email


def update_refresh_schedule(user_id, refresh):
    """Set refresh_schedule"""
    result = database.collection("users").document(user_id)
    if result.get().exists:
        result.update({"refresh_schedule": refresh})


def delete_for_user(user_id):
    """Delete all tasks, events, and blocks for a user"""
    db_batch = database.batch()
    result = (
        database.collection("blocks").where("user_ids", "array_contains", user_id).get()
    )
    for item in result:
        db_batch.delete(item.reference)

    result = database.collection("tasks").where("user_id", "==", user_id).get()
    for item in result:
        db_batch.delete(item.reference)

    result = database.collection("events").where("user_id", "==", user_id).get()
    for item in result:
        db_batch.delete(item.reference)

    db_batch.commit()

    return {"success": True}


def delete_collections(collection_list):
    """Delete all tasks, events, and blocks for a user"""
    db_batch = database.batch()

    if "blocks" in collection_list:
        result = database.collection("blocks").get()
        for item in result:
            db_batch.delete(item.reference)

    if "events" in collection_list:
        result = database.collection("events").get()
        for item in result:
            db_batch.delete(item.reference)

    if "groups" in collection_list:
        result = database.collection("groups").get()
        for item in result:
            db_batch.delete(item.reference)

    if "tasks" in collection_list:
        result = database.collection("tasks").get()
        for item in result:
            db_batch.delete(item.reference)

    db_batch.commit()

    return {"success": True}
