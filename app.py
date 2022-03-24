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
import datetime
from firebase_admin import exceptions, auth

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


@app.route("/establish_session", methods=["POST"])
def session_login():
    # Get the ID token sent by the client
    id_token = request.json["idToken"]
    print(id_token)
    # Set session expiration to 5 days.
    expires_in = datetime.timedelta(days=5)
    try:
        # Create the session cookie. This will also verify the ID token in the process.
        # The session cookie will have the same claims as the ID token.
        session_cookie = auth.create_session_cookie(id_token, expires_in=expires_in)
        response = jsonify({"status": "success"})
        # Set cookie policy for session cookie.
        expires = datetime.datetime.now() + expires_in
        response.set_cookie(
            "session", session_cookie, expires=expires, httponly=True, secure=True
        )
        print("session cookie", session_cookie)
        return response
    except exceptions.FirebaseError as session_error:
        print("except", session_error)
        return abort(401, "Failed to create a session cookie")
