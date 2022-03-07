import pymongo
from pymongo import MongoClient

cluster = MongoClient(
    "mongodb+srv://capstone2022:d2TU1o9kT84Yy3at@cluster0.plj3i.mongodb.net/hourly?retryWrites=true&w=majority"
)
db = cluster["hourly"]
collection = db["users"]
