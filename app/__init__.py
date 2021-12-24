from flask import Flask
from flask_login import LoginManager

app = Flask(__name__, instance_relative_config=True)

app.config.from_object('config')
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


from app import views
from app import database
from app.database import db

db.create_all()
