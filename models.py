# models.py

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# Initialize db
db = SQLAlchemy()

# ------------------------
# User Model
# ------------------------
class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.Text, nullable=False)

    # Set password (hashing)
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    # Verify password
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


# ------------------------
# Plan Model
# ------------------------
class Plan(db.Model):
    __tablename__ = "plans"

    id = db.Column(db.Integer, primary_key=True)
    patient_name = db.Column(db.String(120), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    sex = db.Column(db.String(10), nullable=False)
    stroke_type = db.Column(db.String(50), nullable=False)
    nihss = db.Column(db.Integer, nullable=False)
    affected_side = db.Column(db.String(50), nullable=False)
    weeks_post_stroke = db.Column(db.Integer, nullable=False)
    comorbidities = db.Column(db.String(250), nullable=True)
    goals = db.Column(db.String(250), nullable=True)
    email = db.Column(db.String(120))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False) # No change needed here, this is correct!
    input_data = db.Column(db.Text, nullable=False)
    plan_data = db.Column(db.Text, nullable=False)  # JSON plan data

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    user = db.relationship("User", backref=db.backref("plans", lazy=True))


# ------------------------
# Progress Model
# ------------------------
class Progress(db.Model):
    __tablename__ = "progress"

    id = db.Column(db.Integer, primary_key=True)
    plan_id = db.Column(db.Integer, db.ForeignKey("plans.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    date = db.Column(db.Date, default=lambda: datetime.utcnow().date(), nullable=False)
    walk_speed = db.Column(db.Float, nullable=True)  # m/s
    grip_strength = db.Column(db.Float, nullable=True)  # kg
    adherence = db.Column(db.Integer, nullable=False, default=0)  # sessions completed

    plan = db.relationship("Plan", backref=db.backref("progress", lazy=True))
    user = db.relationship("User", backref=db.backref("progress", lazy=True))
