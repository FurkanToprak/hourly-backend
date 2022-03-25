"""Main Application File"""
import logging
from flask import Flask, request, jsonify, abort
from google.oauth2 import id_token
from google.auth.transport import requests
from flask_cors import CORS
from users import user_routes
from tasks import tasks_routes
from blocks import blocks_routes
from events import events_routes

app = Flask(__name__)
app.logger.setLevel(logging.INFO)
cors = CORS(app, resources={r"*": {"origins": "*"}})


@app.route("/tests/login", methods=["POST"])
def login():
    """Testing login"""
    params = request.json
    email = params["email"]
    name = params["name"]
    start_day = params["startOfDay"]
    end_day = params["endOfDay"]
    return user_routes.login(email, name, start_day, end_day)


@app.route("/users/getSleep", methods=["POST"])
def get_sleep():
    """Get Users Sleep Schedule"""
    params = request.json
    user_id = params["id"]
    return user_routes.get_sleep(user_id)


@app.route("/users/updateSleep", methods=["POST"])
def update_sleep():
    """Update Users Sleep Schedule"""
    params = request.json
    user_id = params["id"]
    start_day = params["startOfDay"]
    end_day = params["endOfDay"]
    return user_routes.update_sleep(user_id, start_day, end_day)


@app.route("/tasks/createTask", methods=["POST"])
def create_task():
    "Creating a task for a user"
    params = request.json
    return tasks_routes.create_task(params)


@app.route("/tasks/getTasks", methods=["POST"])
def get_task():
    "Getting tasks with a user id"
    params = request.json
    return tasks_routes.get_task(params)


@app.route("/tasks/getTaskById", methods=["POST"])
def get_task():
    "Getting task with a task id"
    params = request.json
    return tasks_routes.get_task_by_id(params)


@app.route("/events/createEvent", methods=["POST"])
def create_event():
    "Create an event for a user"
    params = request.json
    return events_routes.create_event(params)


@app.route("/events/getEvents", methods=["POST"])
def get_events():
    "Getting events with a user id"
    params = request.json
    return events_routes.get_events(params)


@app.route("/blocks/getBlocks", methods=["POST"])
def get_block():
    "Getting blocks with a user id"
    params = request.json
    return blocks_routes.get_block(params)


@app.route("/google_auth", methods=["POST"])
def google_auth():
    """Verifies Google OAuth protocols"""
    params = request.json
    token = params["token"]
    user_name = params["name"]
    start_day = params["startOfDay"]
    end_day = params["endOfDay"]
    try:
        idinfo = id_token.verify_oauth2_token(token, requests.Request())
        user_email = idinfo["email"]
        return user_routes.login(user_email, user_name, start_day, end_day)
    except Exception as post_error:  # pylint: disable=broad-except
        # Invalid token
        return str(post_error)


@app.route("/")
def hello_world():
    """Return Hello World"""
    app.logger.info("Hello World Rendered")
    return "<p>Hello, World!</p>"
