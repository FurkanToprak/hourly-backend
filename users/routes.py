"""Routes for Users"""
from flask import jsonify
from users.models import User
from db_connection import database


def login(email, name):
    """Check If user is logged in"""
    user = User().structure()
    result = database.collection("users").where("email", "==", email).get()
    if result:
        send = {"id": result[0].to_dict()["id"]}
    else:
        doc_ref = database.collection("users").document()
        doc_id = doc_ref.id

        user["id"] = doc_id
        user["email"] = email
        user["name"] = name
        database.collection("users").add(user, doc_id)
        send = {"id": doc_id}
        print(doc_id)

    return jsonify(send)
