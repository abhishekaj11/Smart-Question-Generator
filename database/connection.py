from pymongo import MongoClient
import os

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
client = MongoClient(MONGO_URI)

def get_database(db_name: str = "SQG"):
    return client[db_name]

def get_collection(db_name: str, collection_name: str):
    return get_database(db_name)[collection_name]


if __name__ == "__main__":
    db = get_database()
    print("Type of DB:", type(db))
    print("Database Name:", db.name)
