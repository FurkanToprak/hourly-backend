"""Main Application File"""
from flask import Flask, request
from users import routes

app = Flask(__name__)


@app.route("/google_auth", methods=["POST"])
def google_auth():
    """Verifies Google OAuth protocols"""
    payload = request.json
    token = payload["token"]
    user_name = payload["name"]
    try:
        idinfo = id_token.verify_oauth2_token(token, requests.Request())
        user_email = idinfo["email"]
        # TODO: check out what the payload stuff does from idinfo
        return routes.login(user_email, name)
        # TODO: perhaps recieve user data from frontend.
        # TODO: redirect to signup/login as needed
    except Exception as post_error:  # pylint: disable=broad-except
        # Invalid token
        return str(post_error)


@app.route("/")
def hello_world():
    """Return Hello World"""
    return "<p>Hello, World!</p>"
