from flask import Flask
from celery_proj.celeryapp import make_celery

app = Flask(__name__)
celery_app = make_celery(app)


@app.route('/')
def hello_world():
    return 'Hello, World!'
