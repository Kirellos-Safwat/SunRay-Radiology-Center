import psycopg2
from flask_sqlalchemy import SQLAlchemy
from flask import Flask
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
import os

app = Flask(__name__)
connection_string =  'postgresql://hospital_owner:qx6si3HTUwNA@ep-orange-lake-a2ssd1gj-pooler.eu-central-1.aws.neon.tech/hospital?sslmode=require'
connection = psycopg2.connect(connection_string)
app.config['SQLALCHEMY_DATABASE_URI'] = connection_string
app.config['SECRET_KEY'] = '4266af1ee8b1c32ecc9b2d97'
UPLOAD_FOLDER = os.path.join(os.getcwd(), "project", "FlaskProfilePage", "ProfilePage", "static", "uploads")
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
from ProfilePage import routes
