import os
import logging
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, flash, request, session, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import DeclarativeBase

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Set up the database
class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create the Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-key-for-testing")

# Configure the SQLite database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///neighbourhood.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
db.init_app(app)

# Set up Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

# Import models after initializing db to avoid circular imports
with app.app_context():
    from models import User, Task, UserProfile, Feedback
    db.create_all()

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    from models import User
    return db.session.get(User, int(user_id))

# Import forms
from forms import LoginForm, RegistrationForm, TaskRequestForm, VolunteerProfileForm, FeedbackForm

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        from models import User
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('Invalid email or password')
    
    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        from models import User, UserProfile
        # Check if user already exists
        if User.query.filter_by(email=form.email.data).first():
            flash('Email already registered')
            return render_template('register.html', form=form)
        
        # Create new user
        hashed_password = generate_password_hash(form.password.data)
        user = User(
            username=form.username.data,
            email=form.email.data,
            password_hash=hashed_password,
            user_type=form.user_type.data
        )
        db.session.add(user)
        db.session.commit()
        
        # Create user profile
        profile = UserProfile(
            user_id=user.id,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            phone=form.phone.data,
            address=form.address.data
        )
        db.session.add(profile)
        db.session.commit()
        
        flash('Registration successful. Please log in.')
        return redirect(url_for('login'))
    
    return render_template('register.html', form=form)

@app.route('/dashboard')
@login_required
def dashboard():
    from models import Task, User
    
    if current_user.user_type == 'admin':
        # Admin sees all tasks
        tasks = Task.query.all()
        return render_template('admin.html', tasks=tasks)
    
    elif current_user.user_type == 'volunteer':
        # Volunteers see tasks they can help with and tasks they've accepted
        my_tasks = Task.query.filter_by(volunteer_id=current_user.id).all()
        available_tasks = Task.query.filter_by(status='open').all()
        return render_template('dashboard.html', my_tasks=my_tasks, available_tasks=available_tasks)
    
    else:  # recipient
        # Recipients see tasks they've requested
        my_requests = Task.query.filter_by(requester_id=current_user.id).all()
        return render_template('dashboard.html', my_requests=my_requests)

@app.route('/request_help', methods=['GET', 'POST'])
@login_required
def request_help():
    if current_user.user_type != 'recipient' and current_user.user_type != 'admin':
        flash('Only recipients can request help')
        return redirect(url_for('dashboard'))
    
    form = TaskRequestForm()
    if form.validate_on_submit():
        from models import Task
        new_task = Task(
            title=form.title.data,
            category=form.category.data,
            description=form.description.data,
            location=form.location.data,
            preferred_time=form.preferred_time.data,
            requester_id=current_user.id,
            status='open',
            created_at=datetime.now()
        )
        db.session.add(new_task)
        db.session.commit()
        flash('Help request submitted successfully!')
        return redirect(url_for('dashboard'))
    
    return render_template('request_help.html', form=form)

@app.route('/task/<int:task_id>')
@login_required
def task_details(task_id):
    from models import Task, User, Feedback
    
    task = db.session.get(Task, task_id)
    if not task:
        flash('Task not found')
        return redirect(url_for('dashboard'))
    
    # Check permissions
    if (current_user.user_type != 'admin' and 
        current_user.id != task.requester_id and 
        current_user.id != task.volunteer_id and
        task.status != 'open'):
        flash('You do not have permission to view this task')
        return redirect(url_for('dashboard'))
    
    requester = User.query.get(task.requester_id)
    volunteer = User.query.get(task.volunteer_id) if task.volunteer_id else None
    
    # Get feedback if task is completed
    feedback = None
    if task.status == 'completed':
        feedback = Feedback.query.filter_by(task_id=task.id).first()
    
    return render_template('task_details.html', task=task, requester=requester, 
                          volunteer=volunteer, feedback=feedback)

@app.route('/task/<int:task_id>/volunteer', methods=['POST'])
@login_required
def volunteer_for_task(task_id):
    if current_user.user_type != 'volunteer':
        flash('Only volunteers can accept tasks')
        return redirect(url_for('dashboard'))
    
    from models import Task
    task = db.session.get(Task, task_id)
    if not task:
        flash('Task not found')
        return redirect(url_for('dashboard'))
    
    if task.status != 'open':
        flash('This task is no longer available')
        return redirect(url_for('dashboard'))
    
    task.volunteer_id = current_user.id
    task.status = 'assigned'
    task.assigned_at = datetime.now()
    db.session.commit()
    
    flash('You have volunteered for this task!')
    return redirect(url_for('task_details', task_id=task.id))

@app.route('/task/<int:task_id>/complete', methods=['POST'])
@login_required
def complete_task(task_id):
    from models import Task
    
    task = db.session.get(Task, task_id)
    if not task:
        flash('Task not found')
        return redirect(url_for('dashboard'))
    
    # Only the assigned volunteer or admin can mark a task as complete
    if current_user.id != task.volunteer_id and current_user.user_type != 'admin':
        flash('You do not have permission to complete this task')
        return redirect(url_for('dashboard'))
    
    if task.status != 'assigned':
        flash('Only assigned tasks can be marked as complete')
        return redirect(url_for('task_details', task_id=task.id))
    
    task.status = 'completed'
    task.completed_at = datetime.now()
    db.session.commit()
    
    flash('Task marked as complete!')
    return redirect(url_for('task_details', task_id=task.id))

@app.route('/task/<int:task_id>/feedback', methods=['GET', 'POST'])
@login_required
def provide_feedback(task_id):
    from models import Task, Feedback
    
    task = db.session.get(Task, task_id)
    if not task:
        flash('Task not found')
        return redirect(url_for('dashboard'))
    
    # Only the requester can provide feedback
    if current_user.id != task.requester_id:
        flash('Only the requester can provide feedback')
        return redirect(url_for('dashboard'))
    
    if task.status != 'completed':
        flash('Feedback can only be provided for completed tasks')
        return redirect(url_for('task_details', task_id=task.id))
    
    # Check if feedback already exists
    existing_feedback = Feedback.query.filter_by(task_id=task.id).first()
    if existing_feedback:
        flash('You have already provided feedback for this task')
        return redirect(url_for('task_details', task_id=task.id))
    
    form = FeedbackForm()
    if form.validate_on_submit():
        feedback = Feedback(
            task_id=task.id,
            rating=form.rating.data,
            comments=form.comments.data,
            created_at=datetime.now()
        )
        db.session.add(feedback)
        db.session.commit()
        
        flash('Thank you for your feedback!')
        return redirect(url_for('task_details', task_id=task.id))
    
    return render_template('feedback.html', form=form, task=task)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    from models import UserProfile
    
    profile = UserProfile.query.filter_by(user_id=current_user.id).first()
    form = VolunteerProfileForm(obj=profile)
    
    if request.method == 'POST' and form.validate_on_submit():
        profile.first_name = form.first_name.data
        profile.last_name = form.last_name.data
        profile.phone = form.phone.data
        profile.address = form.address.data
        
        if current_user.user_type == 'volunteer':
            profile.skills = form.skills.data
            profile.availability = form.availability.data
            profile.bio = form.bio.data
        
        db.session.commit()
        flash('Profile updated successfully!')
        return redirect(url_for('profile'))
    
    return render_template('profile.html', form=form, profile=profile)

@app.errorhandler(404)
def not_found_error(error):
    return render_template('error.html', error='Page not found'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('error.html', error='An internal error occurred'), 500
