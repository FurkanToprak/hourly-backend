"""Database Connection"""
import firebase_admin
import os
from dotenv import load_dotenv
from firebase_admin import credentials
from firebase_admin import firestore
from pathlib import Path

# path = Path(".env")
# if path.is_file():
load_dotenv()

cred = {
    "type": os.environ["FLASK_TYPE"],
    "project_id": os.environ["FLASK_PROJECT_ID"],
    "private_key_id": os.environ["FLASK_PRIVATE_KEY_ID"],
    "private_key": os.environ["FLASK_PRIVATE_KEY"],
    "client_email": os.environ["FLASK_CLIENT_EMAIL"],
    "client_id": os.environ["FLASK_CLIENT_ID"],
    "auth_uri": os.environ["FLASK_AUTH_URI"],
    "token_uri": os.environ["FLASK_TOKEN_URI"],
    "auth_provider_x509_cert_url": os.environ["FLASK_AUTH_PROVIDER"],
    "client_x509_cert_url": os.environ["FLASK_CLIENT_CERT"],
}
my_credentials = credentials.Certificate(cred)

firebase_admin.initialize_app(my_credentials)

database = firestore.client()
