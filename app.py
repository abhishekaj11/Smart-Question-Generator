from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_cors import CORS
from pymongo import MongoClient
import os, traceback

# Question generator logic
from question_generator import (
    generate_full_paper,
    load_model,
    create_synthetic_dataset_from_course,
    train_classical_model,
    save_model,
)

app = Flask(__name__)
CORS(app)
app.config['JSON_SORT_KEYS'] = False

# MongoDB setup
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
client = MongoClient(MONGO_URI)
db = client["smart_question_db"]
courses_col = db["courses"]
papers_col = db["papers"]

# Load ML model if exists
MODEL_PATH = os.path.join("models", "question_model_ARCH405B.pkl")
vect, clf = None, None
if os.path.exists(MODEL_PATH):
    try:
        vect, clf = load_model(MODEL_PATH)
        print("✅ Loaded saved model from", MODEL_PATH)
    except Exception as e:
        print("⚠️ Could not load model:", e)

# ------------------ Routes ------------------

# Auth page (first page)
@app.route("/")
def auth():
    return render_template("auth.html")

# Redirect to main page after auth
@app.route("/home")
def home():
    return render_template("index.html")

# ---------------- API ----------------

@app.route("/api/courses", methods=["GET"])
def get_courses():
    try:
        courses = list(courses_col.find({}, {"_id": 0}))
        return jsonify({"courses": courses})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    
@app.route("/api/generate-paper", methods=["POST"])
def generate_paper():
    try:
        req = request.json
        course_code = req.get("courseCode", "").strip()  # trim whitespace

        # MongoDB query should match exactly (case-sensitive)
        course = courses_col.find_one({"courseCode": course_code})
        if not course:
            # Try case-insensitive search as fallback
            course = courses_col.find_one({"courseCode": {"$regex": f"^{course_code}$", "$options": "i"}})

        if not course:
            return jsonify({"error": f"No course found for code {course_code}"}), 404

        paper = generate_full_paper(course)
        papers_col.insert_one(paper)

        return jsonify({
            "message": "Question paper generated successfully",
            "paper": paper
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route("/api/add-course", methods=["POST"])
def add_course():
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400

        existing = courses_col.find_one({"courseCode": data.get("courseCode")})
        if existing:
            courses_col.update_one({"courseCode": data["courseCode"]}, {"$set": data})
        else:
            courses_col.insert_one(data)
        return jsonify({"message": "Course saved successfully!"})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route("/api/papers", methods=["GET"])
def get_papers():
    try:
        papers = list(papers_col.find({}, {"_id": 0}))
        return jsonify({"papers": papers})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route("/api/train-model", methods=["POST"])
def train_model():
    try:
        req = request.json
        course_code = req.get("courseCode")

        course = courses_col.find_one({"courseCode": course_code})
        if not course:
            return jsonify({"error": "Course not found"}), 404

        texts, labels = create_synthetic_dataset_from_course(course)
        vect_new, clf_new = train_classical_model(texts, labels)
        save_model(vect_new, clf_new, MODEL_PATH)

        return jsonify({"message": "Model trained and saved successfully"})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# ---------------- Run App ----------------
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
