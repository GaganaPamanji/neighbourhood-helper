from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import login_user, logout_user, current_user, login_required
from datetime import datetime
from app import app, db
from models import User, Request, Task, Feedback
from forms import (LoginForm, RegistrationForm, VolunteerProfileForm, 
                  RequestHelpForm, TaskCompletionForm, FeedbackForm, SearchForm)
from helpers import get_task_status_class

@app.route('/')
def index():
    return render_template('index.html', title='Neighborhood Assistance Program')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid email or password', 'danger')
            return redirect(url_for('login'))
        
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or next_page.startswith('/'):
            next_page = url_for('dashboard')
        return redirect(next_page)
    
    return render_template('login.html', title='Sign In', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            address=form.address.data,
            phone=form.phone.data,
            is_volunteer=form.is_volunteer.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please sign in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html', title='Register', form=form)

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_admin:
        # Admin dashboard
        open_requests = Request.query.filter_by(status='open').count()
        active_tasks = Task.query.filter_by(status='assigned').count()
        completed_tasks = Task.query.filter_by(status='completed').count()
        total_users = User.query.count()
        
        return render_template('dashboard.html', 
                             title='Admin Dashboard',
                             open_requests=open_requests,
                             active_tasks=active_tasks, 
                             completed_tasks=completed_tasks,
                             total_users=total_users)
    
    elif current_user.is_volunteer:
        # Volunteer dashboard
        my_tasks = Task.query.filter_by(volunteer_id=current_user.id).all()
        available_requests = Request.query.filter_by(status='open').all()
        
        return render_template('dashboard.html', 
                             title='Volunteer Dashboard',
                             my_tasks=my_tasks,
                             available_requests=available_requests,
                             get_task_status_class=get_task_status_class)
    
    else:
        # Regular user dashboard
        my_requests = Request.query.filter_by(requester_id=current_user.id).all()
        
        return render_template('dashboard.html', 
                             title='Dashboard',
                             my_requests=my_requests,
                             get_task_status_class=get_task_status_class)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = None
    if current_user.is_volunteer:
        form = VolunteerProfileForm()
        if request.method == 'GET':
            form.skills.data = current_user.skills
            form.availability.data = current_user.availability
            
        if form.validate_on_submit():
            current_user.skills = form.skills.data
            current_user.availability = form.availability.data
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('profile'))
    
    return render_template('profile.html', title='Profile', form=form)

@app.route('/request-help', methods=['GET', 'POST'])
@login_required
def request_help():
    form = RequestHelpForm()
    if form.validate_on_submit():
        help_request = Request(
            title=form.title.data,
            description=form.description.data,
            category=form.category.data,
            requester_id=current_user.id,
            preferred_date=form.preferred_date.data,
            preferred_time=form.preferred_time.data,
            duration=form.duration.data
        )
        db.session.add(help_request)
        db.session.commit()
        
        flash('Your request has been submitted!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('request_help.html', title='Request Help', form=form)

@app.route('/volunteer', methods=['GET', 'POST'])
@login_required
def volunteer():
    if not current_user.is_volunteer:
        flash('You need to register as a volunteer to access this page.', 'warning')
        return redirect(url_for('dashboard'))
    
    form = SearchForm()
    available_requests = Request.query.filter_by(status='open')
    
    if form.validate_on_submit():
        if form.query.data:
            available_requests = available_requests.filter(
                Request.title.contains(form.query.data) | 
                Request.description.contains(form.query.data)
            )
        
        if form.category.data:
            available_requests = available_requests.filter_by(category=form.category.data)
    
    available_requests = available_requests.all()
    
    return render_template('volunteer.html', 
                         title='Volunteer Opportunities', 
                         available_requests=available_requests,
                         form=form)

@app.route('/task/<int:request_id>/accept', methods=['POST'])
@login_required
def accept_task(request_id):
    if not current_user.is_volunteer:
        flash('Only volunteers can accept tasks.', 'danger')
        return redirect(url_for('dashboard'))
    
    help_request = Request.query.get_or_404(request_id)
    
    if help_request.status != 'open':
        flash('This request is no longer available.', 'warning')
        return redirect(url_for('volunteer'))
    
    # Update request status
    help_request.status = 'assigned'
    
    # Create a new task
    task = Task(
        request_id=help_request.id,
        volunteer_id=current_user.id
    )
    
    db.session.add(task)
    db.session.commit()
    
    flash('You have successfully accepted this task!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/task/<int:task_id>', methods=['GET', 'POST'])
@login_required
def task_view(task_id):
    task = Task.query.get_or_404(task_id)
    request_obj = Request.query.get(task.request_id)
    requester = User.query.get(request_obj.requester_id)
    
    # Check permissions
    if not current_user.is_admin and current_user.id != task.volunteer_id and current_user.id != requester.id:
        abort(403)
    
    form = TaskCompletionForm()
    if form.validate_on_submit() and current_user.id == task.volunteer_id:
        task.status = 'completed'
        task.completed_at = datetime.utcnow()
        task.notes = form.notes.data
        request_obj.status = 'completed'
        
        db.session.commit()
        
        flash('Task marked as completed!', 'success')
        return redirect(url_for('feedback', task_id=task.id))
    
    return render_template('task_view.html', 
                         title='Task Details', 
                         task=task, 
                         request=request_obj,
                         requester=requester,
                         form=form)

@app.route('/task/<int:task_id>/feedback', methods=['GET', 'POST'])
@login_required
def feedback(task_id):
    task = Task.query.get_or_404(task_id)
    request_obj = Request.query.get(task.request_id)
    
    # Determine who is giving feedback to whom
    if current_user.id == task.volunteer_id:
        giver_id = current_user.id
        receiver_id = request_obj.requester_id
    elif current_user.id == request_obj.requester_id:
        giver_id = current_user.id
        receiver_id = task.volunteer_id
    else:
        abort(403)
    
    # Check if feedback already given
    existing_feedback = Feedback.query.filter_by(
        task_id=task.id,
        giver_id=giver_id,
        receiver_id=receiver_id
    ).first()
    
    if existing_feedback:
        flash('You have already provided feedback for this task.', 'info')
        return redirect(url_for('dashboard'))
    
    form = FeedbackForm()
    if form.validate_on_submit():
        feedback = Feedback(
            task_id=task.id,
            giver_id=giver_id,
            receiver_id=receiver_id,
            rating=form.rating.data,
            comment=form.comment.data
        )
        
        db.session.add(feedback)
        db.session.commit()
        
        flash('Thank you for your feedback!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('feedback.html', 
                         title='Provide Feedback', 
                         form=form, 
                         task=task)

@app.route('/admin', methods=['GET'])
@login_required
def admin():
    if not current_user.is_admin:
        abort(403)
    
    users = User.query.all()
    requests = Request.query.all()
    tasks = Task.query.all()
    
    return render_template('admin.html', 
                         title='Admin Panel', 
                         users=users,
                         requests=requests,
                         tasks=tasks)

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(403)
def forbidden_error(error):
    return render_template('403.html'), 403

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500
