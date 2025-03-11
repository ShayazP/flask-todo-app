from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime  # Add this import at the top
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import os

# Google Calendar API Settings
SCOPES = ['https://www.googleapis.com/auth/calendar']
CLIENT_SECRETS_FILE = "client_secrets.json"
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'  # Only for development

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'temp'
db = SQLAlchemy(app)

# Login portion 
login_manager = LoginManager()
login_manager.init_app(app) 
login_manager.login_view = 'login'

class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    complete = db.Column(db.Boolean)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    due_date = db.Column(db.DateTime)  # Add this line

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    password = db.Column(db.String()) # will be hashed
    todos = db.relationship('Todo', backref='user', lazy=True)
    google_token = db.Column(db.Text)  # To store Google OAuth token

@app.route("/")
def root():
    return redirect("login")
    
@app.route("/todos")
@login_required
def index():
    # Get todos for current user, sorted by due date
    todo_list = Todo.query.filter_by(user_id=current_user.id).order_by(Todo.due_date.asc()).all()
    return render_template("base.html", todo_list=todo_list, now=datetime.now)

@app.route("/create", methods=["POST"])
@login_required
def create():
    title = request.form.get("title")
    due_date = datetime.strptime(request.form.get("due_date"), '%Y-%m-%dT%H:%M')
    new_todo = Todo(
        title=title,
        complete=False,
        user_id=current_user.id,
        due_date=due_date
    )
    db.session.add(new_todo)
    db.session.commit()
    
    if current_user.google_token:  # Only sync if user has connected Google Calendar
        sync_todo_to_calendar(new_todo)
    
    return redirect(url_for("index"))

@app.route("/delete/<int:todo_id>", methods=["GET"])
@login_required
def delete(todo_id):
    # Only delete if the todo belongs to current user
    todo = Todo.query.filter_by(id=todo_id, user_id=current_user.id).first()
    if todo:
        db.session.delete(todo)
        db.session.commit()
    return redirect(url_for("index"))

@app.route("/update/<int:todo_id>", methods=["GET"])
@login_required
def update(todo_id):
    # Only update if the todo belongs to current user
    todo = Todo.query.filter_by(id=todo_id, user_id=current_user.id).first()
    if todo:
        todo.complete = not todo.complete
        db.session.commit()
    return redirect(url_for("index"))

@login_manager.user_loader
def loader_user(user_id):
    return User.query.get(user_id)

@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # Hash the password before storing
        hashed_password = generate_password_hash(request.form.get("password"))
        user = User(
            name=request.form.get("name"),
            password=hashed_password)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for("login"))
    return render_template("sign_up.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(
            name=request.form.get("name")).first()
        if user is None:
            return redirect(url_for("login"))
        if check_password_hash(user.password, request.form.get("password")):
            login_user(user)
            return redirect(url_for("index"))
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

def get_google_calendar_service():
    if not current_user.google_token:
        return None
    credentials = Credentials.from_authorized_user_info(json.loads(current_user.google_token), SCOPES)
    return build('calendar', 'v3', credentials=credentials)

@app.route('/authorize')
@login_required
def authorize():
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, 
        scopes=SCOPES,
        redirect_uri=url_for('oauth2callback', _external=True)
    )
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true'
    )
    session['state'] = state
    return redirect(authorization_url)

@app.route('/oauth2callback')
@login_required
def oauth2callback():
    state = session['state']
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, 
        scopes=SCOPES,
        state=state,
        redirect_uri=url_for('oauth2callback', _external=True)
    )
    authorization_response = request.url
    flow.fetch_token(authorization_response=authorization_response)
    credentials = flow.credentials
    current_user.google_token = json.dumps({
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    })
    db.session.commit()
    return redirect(url_for('index'))

def sync_todo_to_calendar(todo):
    service = get_google_calendar_service()
    if not service:
        return
    
    event = {
        'summary': todo.title,
        'start': {
            'dateTime': todo.due_date.isoformat(),
            'timeZone': 'America/Los_Angeles',
        },
        'end': {
            'dateTime': todo.due_date.isoformat(),
            'timeZone': 'America/Los_Angeles',
        }
    }
    
    service.events().insert(calendarId='primary', body=event).execute()

if __name__ == "__main__":
    with app.app_context():
        # db.drop_all()  # Comment this out so we don't lose data on restart
        db.create_all()
    app.run(debug=True)