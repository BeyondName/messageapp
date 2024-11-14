import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

# Initialize Flask application and database
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "default_secret_key")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///message_board.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# Database models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(150), nullable=False)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    likes = db.Column(db.Integer, default=0)
    replies = db.relationship("Reply", backref="message", lazy=True)

class Reply(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    message_id = db.Column(db.Integer, db.ForeignKey("message.id"))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.String(200))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# Routes
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        content = request.form.get("content")
        username = session.get("username", "Anonymous")
        user = User.query.filter_by(username=username).first()
        if content:
            message = Message(content=content, user_id=user.id if user else None)
            db.session.add(message)
            db.session.commit()
            flash("Message posted!", "success")
        return redirect(url_for("index"))
    
    messages = Message.query.order_by(Message.timestamp.desc()).all()
    return render_template("index.html", messages=messages)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if User.query.filter_by(username=username).first():
            flash("Username already exists.", "danger")
            return redirect(url_for("register"))
        
        hashed_password = generate_password_hash(password, method="sha256")
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash("Account created successfully!", "success")
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session["username"] = user.username
            flash("Login successful!", "success")
            return redirect(url_for("index"))
        flash("Invalid username or password.", "danger")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("username", None)
    flash("Logged out successfully!", "success")
    return redirect(url_for("index"))

@app.route("/profile/<username>")
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    messages = Message.query.filter_by(user_id=user.id).order_by(Message.timestamp.desc()).all()
    notifications = Notification.query.filter_by(user_id=user.id).order_by(Notification.timestamp.desc()).all()
    return render_template("profile.html", user=user, messages=messages, notifications=notifications)

@app.route("/clear_notifications", methods=["POST"])
def clear_notifications():
    if "username" in session:
        user = User.query.filter_by(username=session["username"]).first()
        Notification.query.filter_by(user_id=user.id).delete()
        db.session.commit()
        flash("Notifications cleared!", "success")
    return redirect(url_for("profile", username=session.get("username")))

@app.route("/like/<int:message_id>", methods=["POST"])
def like_message(message_id):
    if "username" in session:
        message = Message.query.get_or_404(message_id)
        message.likes += 1
        db.session.commit()
        flash("Message liked!", "success")
    else:
        flash("You must be logged in to like messages.", "danger")
    return redirect(url_for("index"))

@app.route("/reply/<int:message_id>", methods=["POST"])
def reply_message(message_id):
    if "username" in session:
        content = request.form.get("content")
        user = User.query.filter_by(username=session["username"]).first()
        if content:
            reply = Reply(content=content, message_id=message_id, user_id=user.id)
            db.session.add(reply)
            db.session.commit()
            flash("Reply posted!", "success")
    else:
        flash("You must be logged in to reply to messages.", "danger")
    return redirect(url_for("index"))

# Database initialization moved here
with app.app_context():
    db.create_all()

# Run the application
if __name__ == "__main__":
    # Use Heroku's assigned port or default to 5000 for local development
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)