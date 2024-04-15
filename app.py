from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import desc, nullslast
from datetime import datetime
import secrets

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = secrets.token_hex(16)  # Generate a secret key

db = SQLAlchemy(app)
migrate = Migrate(app, db)
csrf = CSRFProtect(app)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    completed = db.Column(db.Boolean, default=False, nullable=False)
    due_date = db.Column(db.Date, nullable=True)

    def __repr__(self):
        return f'<Task {self.id}: {self.content}>'

@app.route('/')
def index():
    uncompleted_tasks = Task.query.filter_by(completed=False).order_by(nullslast(desc(Task.due_date))).all()
    completed_tasks = Task.query.filter_by(completed=True).order_by(nullslast(desc(Task.due_date))).all()
    
    return render_template('index.html', uncompleted_tasks=uncompleted_tasks, completed_tasks=completed_tasks)

@app.route('/add', methods=['GET', 'POST'])
def add_task():
    if request.method == 'POST':
        task_content = request.form.get('task')
        task_description = request.form.get('description')
        due_date_str = request.form.get('due_date')
        
        print(f"Due Date String: {due_date_str}")  # Debugging
        try:
            due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date() if due_date_str else None
            print(f"Due Date Object: {due_date}")  # Debugging
        except ValueError as e:
            print(f"Error parsing date: {e}")  # Debugging
        
        new_task = Task(content=task_content, description=task_description, due_date=due_date)
        db.session.add(new_task)
        db.session.commit()
        return redirect(url_for('index'))
    
    return render_template('add_task.html')

@app.route('/edit/<int:task_id>', methods=['GET', 'POST'])
def edit_task(task_id):
    task = Task.query.get(task_id)
    
    if task is None:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        task.content = request.form.get('task')
        task.description = request.form.get('description')
        due_date_str = request.form.get('due_date')
        
        print(f"Due Date String: {due_date_str}")  # Debugging
        try:
            task.due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date() if due_date_str else None
            print(f"Due Date Object: {task.due_date}")  # Debugging
        except ValueError as e:
            print(f"Error parsing date: {e}")  # Debugging
        
        db.session.commit()
        return redirect(url_for('index'))
    
    return render_template('edit_task.html', task=task)


@app.route('/delete/<int:task_id>', methods=['POST', 'DELETE'])
def delete_task(task_id):
    task = Task.query.get(task_id)
    
    if task:
        db.session.delete(task)
        db.session.commit()
    
    return redirect(url_for('index'))

@app.before_request
def before_request():
    if request.method == 'POST' and request.form.get('_method'):
        request.environ['REQUEST_METHOD'] = request.form.get('_method').upper()

@app.route('/complete/<int:task_id>')
def complete_task(task_id):
    task = Task.query.get(task_id)
    
    if task:
        task.completed = True
        db.session.commit()
    
    return redirect(url_for('index'))

@app.route('/incomplete/<int:task_id>')
def incomplete_task(task_id):
    task = Task.query.get(task_id)
    
    if task:
        task.completed = False
        db.session.commit()
    
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
