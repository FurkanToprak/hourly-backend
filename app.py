from flask import Flask

app = Flask(__name__)
#routes
from users import routes

@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"