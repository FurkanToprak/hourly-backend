"""Routes for Users"""
from flask import request, jsonify
from users.models import User
from db_connection import database


def signup():
    """Return user"""
    user = User().structure()
    user["username"] = request.args.get("username")
    user["password"] = request.args.get("password")
    user["email"] = request.args.get("email")

    database.collection("users").add(user)
    return jsonify(user), 200
