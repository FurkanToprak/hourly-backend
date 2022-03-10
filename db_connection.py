"""Database Connection"""
import os
import json
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

my_credentials = credentials.Certificate(json.loads(os.environ["FLASK_FIREBASE_JSON"]))

firebase_admin.initialize_app(my_credentials)

database = firestore.client()
