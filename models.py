from datetime import datetime
from app import db
from flask_login import UserMixin

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    user_type = db.Column(db.String(20), nullable=False)  # 'volunteer', 'recipient', or 'admin'
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # Relationships
    profile = db.relationship('UserProfile', backref='user', uselist=False)
    requested_tasks = db.relationship('Task', backref='requester', 
                                     foreign_keys='Task.requester_id')
    volunteered_tasks = db.relationship('Task', backref='volunteer', 
                                       foreign_keys='Task.volunteer_id')

class UserProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    phone = db.Column(db.String(20))
    address = db.Column(db.String(200))
    bio = db.Column(db.Text)
    skills = db.Column(db.Text)  # Comma-separated list of skills for volunteers
    availability = db.Column(db.Text)  # Text describing availability for volunteers
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)  # e.g., household, errands, companionship, etc.
    description = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(200), nullable=False)
    preferred_time = db.Column(db.String(100))
    status = db.Column(db.String(20), default='open')  # 'open', 'assigned', 'completed', 'cancelled'
    requester_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    volunteer_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.now)
    assigned_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    
    # Relationship
    feedback = db.relationship('Feedback', backref='task', uselist=False)

class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5 rating
    comments = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)
