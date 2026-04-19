import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

# Use MongoDB connection specifically
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/outreach")

client = MongoClient(MONGODB_URI)
try:
    db = client.get_database()
except Exception:
    db = client["outreach"]

def get_db():
    try:
        yield db
    finally:
        pass
