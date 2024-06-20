import psycopg2
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, session, abort, redirect, request
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
import os
from flask_mail import Mail, Message
import pathlib
from google_auth_oauthlib.flow import Flow


app = Flask(__name__)
connection_string =  'postgresql://hospital_owner:qx6si3HTUwNA@ep-orange-lake-a2ssd1gj.eu-central-1.aws.neon.tech/hospital?sslmode=require'
connection = psycopg2.connect(connection_string)
app.config['SQLALCHEMY_DATABASE_URI'] = connection_string
app.config['SECRET_KEY'] = '4266af1ee8b1c32ecc9b2d97'

# UPLOAD_FOLDER = os.path.join(os.getcwd(),"ProfilePage", "static", "uploads")
UPLOAD_FOLDER = os.path.join(os.getcwd(), "project","FlaskProfilePage","ProfilePage", "static", "uploads")
# print(os.getcwd())
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'rawanwalid978'
app.config['MAIL_PASSWORD'] = 'cugi bixb rqdu cwpb'
mail = Mail(app)
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
GOOGLE_CLIENT_ID = "362697938388-1bn92qqk4vrvn38i00d5h17qrgd1cfiv.apps.googleusercontent.com"
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
client_secrets_file = os.path.join(pathlib.Path(__file__).parent, "client_secret.json")

flow = Flow.from_client_secrets_file(
    client_secrets_file=client_secrets_file,
    scopes=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email", "openid"],
    redirect_uri="http://127.0.0.1:5000/callback"
)

from ProfilePage import routes
