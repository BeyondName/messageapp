from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///message_board.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'
db = SQLAlchemy(app)

# Database models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    messages = db.relationship('Message', backref='author', lazy=True)
    notifications = db.relationship('Notification', backref='user', lazy=True)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # Nullable for anonymous posts
    replies = db.relationship('Reply', backref='message', lazy=True)
    likes = db.Column(db.Integer, default=0)

class Reply(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    message_id = db.Column(db.Integer, db.ForeignKey('message.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.String(200), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# Initialize the database manually
def create_tables():
    with app.app_context():
        db.create_all()

# Call create_tables once at the start of the application
create_tables()

# User registration
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        hashed_password = generate_password_hash(password, method='sha256')
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash("Username already taken", "danger")
            return redirect(url_for("register"))

        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash("Registration successful! Please log in.", "success")
        return redirect(url_for("login"))
    return render_template("register.html")

# User login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session["user_id"] = user.id
            session["username"] = user.username
            flash("Logged in successfully", "success")
            return redirect(url_for("index"))
        else:
            flash("Invalid username or password", "danger")
            return redirect(url_for("login"))
    return render_template("login.html")

# User logout
@app.route("/logout")
def logout():
    session.pop("user_id", None)
    session.pop("username", None)
    flash("Logged out successfully", "success")
    return redirect(url_for("index"))

# Home page - Message board
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        content = request.form.get("content")
        user_id = session.get("user_id")
        user = User.query.get(user_id) if user_id else None  # Get the logged-in user or None for anonymous

        if content:
            message = Message(content=content, author=user)
            db.session.add(message)
            db.session.commit()
            flash("Message posted successfully", "success")
        return redirect(url_for("index"))

    messages = Message.query.order_by(Message.timestamp.desc()).all()
    return render_template("index.html", messages=messages)

# Profile page with notifications
@app.route("/profile/<username>")
def profile(username):
    user = User.query.filter_by(username=username).first()
    if user:
        notifications = user.notifications
        return render_template("profile.html", user=user, messages=user.messages, notifications=notifications)
    else:
        flash("User not found!", "danger")
        return redirect(url_for("index"))

# API for adding a reply
@app.route("/reply/<int:message_id>", methods=["POST"])
def reply(message_id):
    content = request.form.get("content")
    user_id = session.get("user_id")
    user = User.query.get(user_id) if user_id else None  # Logged-in user or None for anonymous replies

    if content:
        reply = Reply(content=content, message_id=message_id, user_id=user_id)
        db.session.add(reply)

        message = Message.query.get(message_id)
        if message and message.user_id and message.user_id != user_id:
            notification = Notification(message="You received a reply", user_id=message.user_id)
            db.session.add(notification)

        db.session.commit()
        flash("Reply added successfully", "success")
    return redirect(url_for("index"))

# API for liking a message
@app.route("/like/<int:message_id>", methods=["POST"])
def like(message_id):
    message = Message.query.get(message_id)
    if message:
        message.likes += 1
        db.session.commit()
        flash("Message liked!", "success")
    return redirect(url_for("index"))

# Clear notifications after viewing
@app.route("/clear_notifications", methods=["POST"])
def clear_notifications():
    user_id = session.get("user_id")
    if user_id:
        Notification.query.filter_by(user_id=user_id).delete()
        db.session.commit()
        flash("Notifications cleared", "success")
    return redirect(url_for("profile", username=session.get("username")))

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)