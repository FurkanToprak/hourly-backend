"""Main Application File"""
import logging
from flask import Flask, request
from google.oauth2 import id_token
from google.auth.transport import requests
from flask_cors import CORS

app = Flask(__name__)
app.logger.setLevel(logging.INFO)
cors = CORS(app, resources={r"*": {"origins": "*"}})


@app.route("/")
def hello_world():
    """Return Hello World"""
    app.logger.info("Hello World Rendered")
    return "<p>Hello, World!</p>"


@app.route("/google_auth", methods=["POST"])
def google_auth():
    """Verifies Google OAuth protocols"""
    payload = request.json
    token = payload["token"]
    # client_id = payload["clientId"]
    try:
        idinfo = id_token.verify_oauth2_token(token, requests.Request())
        userid = idinfo["sub"]
        app.logger.info("User ID - ", userid)
        return "Success"
    except Exception as post_error:  # pylint: disable=broad-except
        # Invalid token
        return str(post_error)
