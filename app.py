from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime

app = Flask(__name__)

# In-memory "database" to store messages, user profiles, and replies
messages = []
users = {}

# Home page - Message board
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # Get message content, username, and optional reply ID from the form
        content = request.form.get("content")
        username = request.form.get("username") or "Anonymous"
        reply_to = request.form.get("reply_to")

        if content:
            # Add the message with the username and timestamp to the messages list
            message = {
                "id": len(messages) + 1,
                "username": username,
                "content": content,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "replies": []
            }
            if reply_to:
                # Find the message to reply to and add the reply
                for msg in messages:
                    if msg["id"] == int(reply_to):
                        msg["replies"].append(message)
                        break
            else:
                # Add as a new message
                messages.append(message)
        return redirect(url_for("index"))

    # Display messages in reverse order (newest first)
    return render_template("index.html", messages=reversed(messages))

# Registration page
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        if username:
            users[username] = {"username": username}
            return redirect(url_for("profile", username=username))
    return render_template("register.html")

# Login page
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        if username in users:
            return redirect(url_for("profile", username=username))
        else:
            return "User not found!", 404
    return render_template("login.html")

# Profile page
@app.route("/profile/<username>")
def profile(username):
    user = users.get(username)
    if user:
        return render_template("profile.html", user=user)
    else:
        return "User not found!", 404

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)