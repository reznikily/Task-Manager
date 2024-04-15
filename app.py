from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
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

    def __repr__(self):
        return f'<Task {self.id}: {self.content}>'

@app.route('/')
def index():
    tasks = Task.query.all()
    return render_template('index.html', tasks=tasks)

@app.route('/add', methods=['GET', 'POST'])
def add_task():
    if request.method == 'POST':
        task_content = request.form.get('task')
        new_task = Task(content=task_content)
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

if __name__ == '__main__':
    app.run(debug=True)
