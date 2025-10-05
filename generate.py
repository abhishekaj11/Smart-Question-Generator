from flask import Flask, jsonify

app = Flask(__name__)

@app.route("/generate", methods=["GET"])
def generate():
    return jsonify({"message": "Hello from backend!"})


@app.route("/generate", methods=["GET"])
def generate():
    syllabus = db["syllabus"].find_one({"courseCode": "CS101"})
    paper = generate_question_paper(syllabus)
    return jsonify({"question_paper": paper})



if __name__ == "__main__":
    app.run(debug=True)
