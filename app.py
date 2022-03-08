"""Main Application File"""
from flask import Flask, request
from google.oauth2 import id_token
from google.auth.transport import requests
from flask_cors import CORS

app = Flask(__name__)
cors = CORS(app, resources={r"*": {"origins": "*"}})


@app.route("/")
def hello_world():
    """Return Hello World"""
    return "<p>Hello, World!</p>"


@app.route("/google_auth", methods=["POST"])
def google_auth():
    """Verifies Google OAuth protocols"""
    payload = request.json
    token = payload["token"]
    client_id = payload["clientId"]
    try:
        idinfo = id_token.verify_oauth2_token(token, requests.Request(), client_id)
        userid = idinfo["sub"]
        print(userid)
        return "Success"
    except Exception as post_error:  # pylint: disable=broad-except
        # Invalid token
        return str(post_error)
