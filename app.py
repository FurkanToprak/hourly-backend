"""Main Application File"""
import logging
import os
from flask import Flask, request, jsonify
from flask_mail import Mail
from google.oauth2 import id_token
from google.auth.transport import requests
from flask_cors import CORS
from scheduling.schedule import Schedule
from users import user_routes
from tasks import tasks_routes
from blocks import blocks_routes
from events import events_routes
from groups import groups_routes


app = Flask(__name__)
app.config.update(
    MAIL_SERVER="smtp.gmail.com",
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME=os.environ["MAIL_USERNAME"],
    MAIL_PASSWORD=os.environ["MAIL_PASSWORD"],
    MAIL_DEBUG=False,
)
mail = Mail(app)
app.logger.setLevel(logging.INFO)
cors = CORS(app, resources={r"*": {"origins": "*"}})


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
    except Exception as post_error:
        # Invalid token
        return str(post_error)


@app.route("/users/getSleep", methods=["POST"])
def get_sleep():
    """Get Users Sleep Schedule"""
    params = request.json
    user_id = params["user_id"]
    return user_routes.get_sleep(user_id)


@app.route("/users/updateSleep", methods=["POST"])
def update_sleep():
    """Update Users Sleep Schedule"""
    params = request.json
    user_id = params["user_id"]
    start_day = params["startOfDay"]
    end_day = params["endOfDay"]
    return user_routes.update_sleep(user_id, start_day, end_day)


@app.route("/users/deleteEverything", methods=["POST"])
def delete_everything():
    """Delete all of a user's blocks, tasks, and events"""
    params = request.json
    user_id = params["user_id"]

    return user_routes.delete_everything(user_id=user_id)


@app.route("/tasks/createTask", methods=["POST"])
def create_task():
    "Creating a task for a user"
    params = request.json
    return tasks_routes.create_task(params)


@app.route("/tasks/updateTask", methods=["POST"])
def update_task():
    "Send completed blocks to update the task"
    params = request.json
    return tasks_routes.update_task_hours(params)


@app.route("/tasks/completeTask", methods=["POST"])
def complete_task():
    "Mark a task as entirely complete"
    params = request.json
    if tasks_routes.completed_task(task_id=params["task_id"]):
        return {"success": True}
    else:
        return {"success": False}


@app.route("/tasks/deleteTask", methods=["POST"])
def delete_task():
    "Delete tasks with a task id"
    params = request.json
    return tasks_routes.delete_task(params["task_id"])


@app.route("/tasks/getUserTasks", methods=["POST"])
def get_user_tasks():
    "Getting user tasks with a user id"
    params = request.json
    return tasks_routes.get_tasks(user_id=params["user_id"])


@app.route("/tasks/getTaskById", methods=["POST"])
def get_task_by_id():
    "Getting task with a task id"
    params = request.json
    return tasks_routes.get_task_by_id(params["task_id"])


@app.route("/tasks/cramTask", methods=["POST"])
def cram_task():
    "Mark task as cram"
    params = request.json
    return tasks_routes.cram_task(params["task_id"])


@app.route("/events/createEvent", methods=["POST"])
def create_event():
    "Create an event for a user"
    params = request.json
    return events_routes.create_event(params)


@app.route("/events/getEvents", methods=["POST"])
def get_events():
    "Getting events with a user id"
    params = request.json
    return events_routes.get_events(params["user_id"])


@app.route("/events/deleteEvent", methods=["POST"])
def delete_event():
    "Delete event with a event id"
    params = request.json
    return events_routes.delete_event(params["event_id"])


@app.route("/schedule", methods=["POST"])
def schedule_tasks():
    "Auto Scheduler"
    print("Scheduling")
    user_id = request.json["user_id"]
    schedule = Schedule(user_id)
    schedule.scheduler()
    failed, message = schedule.get_message()
    return jsonify(failed=failed, message=message)


@app.route("/blocks/getBlocks", methods=["POST"])
def get_blocks():
    "Getting blocks with a user id"
    params = request.json
    return blocks_routes.get_blocks(user_id=params["user_id"])


@app.route("/blocks/expiredSubTasks", methods=["POST"])
def expired_sub_tasks():
    "Return sub tasks that have expired"
    params = request.json
    return blocks_routes.expired_sub_tasks(user_id=params["user_id"])


@app.route("/groups/createGroup", methods=["POST"])
def create_group():
    """Create Group Function"""
    params = request.json
    return groups_routes.create_group(params)


@app.route("/groups/getGroupInfo", methods=["POST"])
def get_group_info():
    """Create Group Function"""
    params = request.json
    return groups_routes.get_group_info(group_id=params["group_id"])


@app.route("/groups/getUsers", methods=["POST"])
def get_group_users():
    """Get all of a users groups"""
    params = request.json
    return groups_routes.get_group_members(group_id=params["group_id"])


@app.route("/groups/getUsersGroups", methods=["POST"])
def get_users_groups():
    """Get all of a users groups"""
    params = request.json
    return groups_routes.get_users_groups(user_id=params["user_id"])


@app.route("/groups/getUsersLabels", methods=["POST"])
def get_users_labels():
    """Get all of a users groups"""
    params = request.json
    return groups_routes.get_labels(user_id=params["user_id"])


@app.route("/groups/joinGroup", methods=["POST"])
def join_group():
    """Join Group Function"""
    params = request.json
    return groups_routes.join_group(
        user_id=params["user_id"], group_id=params["group_id"]
    )


@app.route("/groups/leaveGroup", methods=["POST"])
def leave_group():
    """Leave Group Function"""
    params = request.json
    return groups_routes.leave_group(
        user_id=params["user_id"], group_id=params["group_id"]
    )


@app.route("/groups/getStats", methods=["POST"])
def get_group_stats():
    """Get Group Stats"""
    params = request.json
    return groups_routes.calculate_stats(group_id=params["group_id"])


@app.route("/groups/getCollaborators", methods=["POST"])
def get_group_collaborators():
    """Get group members searching for a collaborator"""
    params = request.json
    return groups_routes.get_collaborators(group_id=params["group_id"])


@app.route("/groups/placeCollaborator", methods=["POST"])
def place_collaborators():
    """Place user in collaborator list"""
    params = request.json
    return groups_routes.place_collaborator(
        user_id=params["user_id"],
        user_name=params["user_name"],
        group_id=params["group_id"],
    )


@app.route("/groups/checkCollaborators", methods=["POST"])
def check_collaborators():
    """Check user collab compatiblity then create events and notify"""
    params = request.json
    return groups_routes.check_collaborators(
        user_id_1=params["user_id_1"],
        user_id_2=params["user_id_2"],
        name_1=params["name_1"],
        name_2=params["name_2"],
        group_id=params["group_id"],
    )


# Present only for testing purposes
# Will be called internally
@app.route("/groups/getTasks", methods=["POST"])
def get_group_tasks():
    """Get Group Tasks"""
    params = request.json
    return groups_routes.get_group_tasks(group_id=params["group_id"])


# Present only for testing purposes
# Will be called internally
def send_mail():
    """Send Email Function"""
    params = request.json
    try:
        mail.send_message(
            "Collaborator Found!",
            sender=os.environ["MAIL_USERNAME"],
            recipients=[params["email"]],
            body="We found you a collaborator!",
        )
        return {"success": True}
    except Exception:
        return {"success": False}


@app.route("/")
def hello_world():
    """Return Hello World"""
    app.logger.info("Hello World Rendered")
    return "<p>Hello, World!</p>"
