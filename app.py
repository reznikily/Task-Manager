from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import desc, nullslast
from datetime import datetime
import secrets
from forms import RegistrationForm, LoginForm, TaskForm
from models import db, User, Task
from dateutil import parser

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = secrets.token_hex(16)  # Generate a secret key

db.init_app(app)

migrate = Migrate(app, db)
csrf = CSRFProtect(app)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect('/')
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if not user:
            user = User(username=form.username.data)
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            flash('Registration successful. Please log in.', 'success')
            return redirect(url_for('login'))
        else:
            flash("Username already exists.", 'error')
    else:
        flash("Passwords are not the same.", 'error')
    
    return render_template('register.html', title='Sign Up', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect('/')
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            session['user_id'] = user.id
            session['username'] = user.username
            flash('Login successful.', 'success')
            return redirect(url_for('tasks'))
        else:
            flash('Invalid username or password.', 'danger')
    return render_template('login.html', title='Log In', form=form)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

def get_tasks_by_user_id(user_id):
    return Task.query.filter_by(user_id=user_id).all()

@app.route('/', methods=['GET', 'POST'])
def tasks():
    if 'user_id' not in session:
        flash('Please log in first.', 'danger')
        return redirect(url_for('login'))

    user_id = session['user_id']
    uncompleted_tasks = Task.query.filter_by(user_id=user_id, completed=False).all()
    completed_tasks = Task.query.filter_by(user_id=user_id, completed=True).all()

    return render_template('tasks.html', username=session['username'], uncompleted_tasks=uncompleted_tasks, completed_tasks=completed_tasks)

@app.route('/add_task', methods=['GET', 'POST'])
def add_task():
    if 'user_id' not in session:
        flash('Please log in first.', 'danger')
        return redirect(url_for('login'))
    
    form = TaskForm()
    
    if form.validate_on_submit():
        user_id = session['user_id']

        new_task = Task(
            name=form.name.data,
            description=form.description.data,
            due_date=form.due_date.data,
            user_id=user_id
        )
        
        db.session.add(new_task)
        db.session.commit()
        
        flash('Task added successfully.', 'success')
        return redirect(url_for('tasks'))
    else:
        flash('Date can not be empty.', 'error')
    
    return render_template('add_task.html', username=session['username'], form=form)

@app.route('/edit_task/<int:task_id>', methods=['GET', 'POST'])
def edit_task(task_id):
    if 'user_id' not in session:
        flash('Please log in first.', 'danger')
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    task = Task.query.filter_by(id=task_id, user_id=user_id).first_or_404()
    
    if request.method == 'POST':
        task.name = request.form['name']
        task.description = request.form['description']
        task.due_date = parser.parse(request.form['due_date'])
        
        db.session.commit()
        flash('Task updated successfully.', 'success')
        return redirect(url_for('tasks'))
    
    return render_template('edit_task.html', username=session['username'], task=task)

@app.route('/mark_completed/<int:task_id>', methods=['GET', 'POST'])
def mark_completed(task_id):
    if 'user_id' not in session:
        flash('Please log in first.', 'danger')
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    task = Task.query.filter_by(id=task_id, user_id=user_id).first_or_404()
    
    task.completed = True
    db.session.commit()
    flash('Task marked as completed.', 'success')
    return redirect(url_for('tasks'))

@app.route('/delete_task/<int:task_id>', methods=['GET', 'POST'])
def delete_task(task_id):
    if 'user_id' not in session:
        flash('Please log in first.', 'danger')
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    task = Task.query.filter_by(id=task_id, user_id=user_id).first_or_404()
    
    db.session.delete(task)
    db.session.commit()
    flash('Task deleted successfully.', 'success')
    return redirect(url_for('tasks'))

@app.route('/mark_incomplete/<int:task_id>', methods=['GET', 'POST'])
def mark_incomplete(task_id):
    if 'user_id' not in session:
        flash('Please log in first.', 'danger')
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    task = Task.query.filter_by(id=task_id, user_id=user_id).first_or_404()
    
    task.completed = False
    db.session.commit()
    
    flash('Task marked as incomplete.', 'success')
    return redirect(url_for('tasks'))

@app.before_request
def before_request():
    if request.method == 'POST' and request.form.get('_method'):
        request.environ['REQUEST_METHOD'] = request.form.get('_method').upper()

if __name__ == '__main__':
    app.run(debug=True)
