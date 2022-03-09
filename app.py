"""Main Application File"""
from flask import Flask
from users import routes

app = Flask(__name__)


@app.route("/users/signup", methods=["POST"])
def signup():
    """Route to sign up"""
    return routes.signup()


@app.route("/")
def hello_world():
    """Return Hello World"""
    return "<p>Hello, World!</p>"
