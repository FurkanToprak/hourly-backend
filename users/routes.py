from flask import Flask
from app import app
from users.models import User

@app.route('/signup', methods=['GET'])

def signup(): 
  return User().signup()


