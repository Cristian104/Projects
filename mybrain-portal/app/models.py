from app.extensions import db
from flask_login import UserMixin
from sqlalchemy.sql import func
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    # 👇 THIS LINE WAS MISSING. Add it to fix the login crash.
    email = db.Column(db.String(150), unique=True, nullable=True)
    password = db.Column(db.String(150), nullable=False)

    # Relationships
    tasks = db.relationship('Task', backref='user', lazy=True)
    habits = db.relationship('TaskHistory', backref='user', lazy=True)
    role = db.Column(db.String(20), default='user')  # Options: 'user', 'dev'
    # Tracks if user is on Day 1, Day 2, etc.
    current_gym_day = db.Column(db.Integer, default=1)


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    priority = db.Column(db.String(20), default='normal')
    category = db.Column(db.String(50), default='general')
    complete = db.Column(db.Boolean, default=False)
    created_date = db.Column(db.DateTime(timezone=True), default=func.now())
    due_date = db.Column(db.DateTime(timezone=True), nullable=True)
    last_completed = db.Column(db.DateTime(timezone=True), nullable=True)

    # Visuals
    color = db.Column(db.String(20), default='#3b5bdb')
    recurrence = db.Column(db.String(20), default='none')
    is_habit = db.Column(db.Boolean, default=False)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


class TaskHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)
    completed_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='completed')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


class UserModuleAccess(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    module = db.Column(db.String(30), nullable=False)  # 'gym','nutrition','tasks','applications'
    enabled = db.Column(db.Boolean, default=True)
    __table_args__ = (db.UniqueConstraint('user_id', 'module', name='_user_module_uc'),)


def user_has_module(user, module):
    """Returns True if user has access to the given module (default: True if no record)."""
    rec = UserModuleAccess.query.filter_by(user_id=user.id, module=module).first()
    return rec.enabled if rec else True


class AgentMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    agent_id = db.Column(db.String(30), nullable=False)   # 'main', 'peccata', etc.
    role = db.Column(db.String(10), nullable=False)        # 'user' | 'agent'
    source = db.Column(db.String(20), default='web')       # 'web' | 'telegram'
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)


class AppEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    url = db.Column(db.String(255), nullable=False)
    icon = db.Column(db.String(50), default='fa-globe')  # FontAwesome class name
    color = db.Column(db.String(20), default='#3A7D52')
    description = db.Column(db.String(200))
    order_index = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
