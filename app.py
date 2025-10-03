from flask import Flask, request, render_template, redirect, url_for
from database.connection import get_database  

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def register():
    collection = get_database("SQG")

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        if not email or not password:
            return "❌ Email or password missing!"

        existing_user = collection.find_one({"email": email})
        if existing_user:
            return "⚠️ User already registered!"

        collection.insert_one({"email": email, "password": password})
        return redirect(url_for("home", user=email))  # 👈 pass email

    return render_template("index.html")


@app.route("/home")
def home():
    user = request.args.get("user")  # 👈 fetch email from URL
    return render_template("home.html", user=user)


if __name__ == "__main__":
    app.run(debug=True)
