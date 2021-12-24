from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired
from flask_login import current_user, login_user, UserMixin, login_user, login_required,logout_user
from argon2 import argon2_hash
from app import login_manager
from app.database import db, Authentication
from base64 import b64encode,b64decode




@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

def login_req(func):
    login_required(func)
    

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])

def logout():
    logout_user()

class User(UserMixin):
    def __init__(self, username, password=""):
        self.username = username
        # Change the salt on your deployment
        self.password = b64encode(argon2_hash(password, "9247v1Z5y6Xnaxs")).decode()
        self.id = ""

    def get(user_id):
        if (user := Authentication.query.filter_by(id = user_id).first()) is not None:
            return User(user.user)

    def register(self):
        new_user = Authentication(user = self.username, password = self.password)
        try:
            db.session.add(new_user)
            db.session.commit()
            return True
        except Exception as e:
            print(e)
            return None

    def check_username(self):
        u = Authentication.query.filter_by(user=self.username).first()
        return self

    def check_password(self):
        if (user := Authentication.query.filter(Authentication.user == self.username, Authentication.password == self.password).first()) is not None:
            print("Authenticated!")
            self.id = user.id
            return True
        return None
