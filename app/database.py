from app import app
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{app.config["DATABASE_FILE"]}'
app.config['SQLALCHEMY_BINDS'] = {'API': f'sqlite://'}


db = SQLAlchemy(app)

class PingCastle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=False, nullable=False)
    privatekey = db.Column(db.String(4000), unique=True, nullable=False)
    apikey = db.Column(db.String(128), unique=True, nullable=False)
    filepath = db.Column(db.String(255), unique=True, nullable=True)
    link = db.Column(db.String(20), unique=True, nullable=True)
    date = db.Column(db.DateTime, unique=False , nullable=False, default=datetime.utcnow)

class Authentication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(39), unique=True, nullable=False)
    password = db.Column(db.String(512), unique=False, nullable=False)

# memory only
class APICastle(db.Model):
    __bind_key__ = 'API'
    id = db.Column(db.Integer, primary_key=True)
    ip = db.Column(db.String(39), unique=False, nullable=False)
    apikey = db.Column(db.String(128), unique=True, nullable=False)
