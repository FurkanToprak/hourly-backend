"""Main Application File"""
import logging
from flask import Flask, request
from google.oauth2 import id_token
from google.auth.transport import requests
from flask_cors import CORS
from users import user_routes
from items import item_routes

app = Flask(__name__)
app.logger.setLevel(logging.INFO)
cors = CORS(app, resources={r"*": {"origins": "*"}})


@app.route("/tests/login", methods=["POST"])
def login():
    """Testing login"""
    payload = request.json
    print(payload["email"], payload["name"])
    return user_routes.login(payload["email"], payload["name"])


# Routes for items


@app.route("/items/createItem", methods=["POST"])
def createItem():
    params = request.json
    return item_routes.createItem(params)


# Routes for Authorization


@app.route("/google_auth", methods=["POST"])
def google_auth():
    """Verifies Google OAuth protocols"""
    payload = request.json
    token = payload["token"]
    user_name = payload["name"]
    try:
        idinfo = id_token.verify_oauth2_token(token, requests.Request())
        user_email = idinfo["email"]

        return user_routes.login(user_email, user_name)
    except Exception as post_error:  # pylint: disable=broad-except
        # Invalid token
        return str(post_error)


@app.route("/")
def hello_world():
    """Return Hello World"""
    app.logger.info("Hello World Rendered")
    return "<p>Hello, World!</p>"
