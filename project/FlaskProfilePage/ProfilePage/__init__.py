import psycopg2
from flask_sqlalchemy import SQLAlchemy
from flask import Flask
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
import os
from flask_mail import Mail

app = Flask(__name__)
connection_string =  'postgresql://hospital_owner:qx6si3HTUwNA@ep-orange-lake-a2ssd1gj-pooler.eu-central-1.aws.neon.tech/hospital?sslmode=require'
connection = psycopg2.connect(connection_string)
app.config['SQLALCHEMY_DATABASE_URI'] = connection_string
app.config['SECRET_KEY'] = '4266af1ee8b1c32ecc9b2d97'

UPLOAD_FOLDER = os.path.join(os.getcwd(), "ProfilePage", "static", "uploads")
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('DB_USER')
app.config['MAIL_PASSWORD'] = os.environ.get('DB_PASS')
mail = Mail(app)
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
from ProfilePage import routes
