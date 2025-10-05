
from pymongo import MongoClient
from connection import get_database,get_collection
db = get_database("SQG")
collection = db["syllabusC"]


def get_syllabus(course_code):
    """
    client = MongoClient("mongodb://localhost:27017/")
    db = client["college_database"]  
    collection = db["syllabus"]     
    """
    
      

    syllabus = collection.find_one({"courseCode": course_code}, {"_id": 0}) 

    if not syllabus:
        print(f"No syllabus found for {course_code}")
        return None

    return syllabus
