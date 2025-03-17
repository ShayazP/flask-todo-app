# Flask Todo Application

A cloud-based Todo application built with Flask that allows users to create accounts, manage tasks, and track due dates.

## Features
- User authentication (register, login, logout)
- Create, update, and delete todos
- Due date tracking for tasks
- Task completion status
- Overdue task highlighting
- Secure password hashing
- User-specific todo lists

## Prerequisites
- Python 3.x
- pip (Python package installer)

## How to run the program

1. Create a virtual environment:
```bash
python -m venv venv
```

2. Activate the virtual environment in the root of the project folder:
- On Windows:
```bash
venv\Scripts\activate
```
- On macOS/Linux:
```bash
source venv/bin/activate
```

3. Install flask
```bash
pip install flask
```

4. Install these dependencies
```bash
pip install flask-sqlalchemy
```
```bash
pip install python-dotenv
```
```bash
pip install flask-login
```

5. Go to the flask-todo-app-main folder (if already in it then ignore this and go to step 6)
```bash
cd flask-todo-app-main
```

6. Run the application.py file
```bash
python application.py
```
7. In the terminal you will see two links. Click on the first one that should say
```bash
Running on http://127.0.0.1:8000
```
8. Once you open this link in the browser, you then can use the application locally.



9. To use the live version you can visit
```bash
http://cloud-todo.us-west-2.elasticbeanstalk.com/
```

## High Level Design

![HLD](https://github.com/ShayazP/flask-todo-app/blob/57f74f72c86729c32b0e4e80a5e69438b8cb2c35/Cloud%20To-Do%20Architecture%20Design%20Diagram.png)
