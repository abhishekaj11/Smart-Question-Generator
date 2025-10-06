from flask import Flask, request, render_template, redirect, url_for
import json
from backend.database.connection import get_database 
from backend.generate_questions import generate_question_paper

app = Flask(__name__)
"""
@app.route("/", methods=["GET", "POST"])
def register():
    collection = get_database("SQG")["Login"]


    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        if not email or not password:
            return "❌ Email or password missing!"

        existing_user = collection.find_one({"email": email})
        if existing_user:
            return "⚠️ User already registered!"

        user = {"email": email, "password": password}

        collection.insert_one(user)
        return redirect(url_for("home", user=email))  # 👈 pass email

    return render_template("index.html")
"""

@app.route("/home")
def home():
    user = request.args.get("user")  # 👈 fetch email from URL
    return render_template("home.html", user=user)


@app.route("/generate", methods=["GET"])
def generate():
    coursecode = request.form.get("subcode")
    collection = get_database("SQG")["syllabusC"]
    syllabus = collection.find_one({"courseCode": coursecode})
    paper = generate_question_paper(syllabus)
    return jsonify({"question_paper": paper})



if __name__ == "__main__":
    app.run(debug=True)
