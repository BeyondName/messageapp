from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime
import os

app = Flask(__name__)

# A simple in-memory "database" to store messages
messages = []

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # Get message content and add to messages list
        content = request.form.get("content")
        if content:
            messages.append({
                "content": content,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
        return redirect(url_for("index"))

    # Display messages in reverse order (newest first)
    return render_template("index.html", messages=reversed(messages))

if __name__ == "__main__":
    # Heroku assigns a dynamic port, so we need to use it
    port = int(os.environ.get("PORT", 5000))  # Default to 5000 if not found
    app.run(debug=False, host="0.0.0.0", port=port)  # Listen on all IPs and use the dynamic port