from ProfilePage import db, login_manager
from ProfilePage import bcrypt
from flask_login import UserMixin


@login_manager.user_loader
def load_user(user_id):
    return Credentials.query.get(int(user_id))


class Credentials(db.Model, UserMixin):
    id = db.Column(db.Integer(), primary_key=True)
    fname = db.Column(db.String(length=15), nullable=False)
    lname = db.Column(db.String(length=15), nullable=False)
    email = db.Column(db.String(length=30), nullable=False, unique=True)
    phone = db.Column(db.String(length=13), nullable=False, unique=True)
    password_hash = db.Column(db.String(length=60), nullable=False)  # Will be changed later to false
    profile_picture = db.Column(db.String(length=255))
    is_admin = db.Column(db.Boolean(), default=False)

    @property
    def password(self):
        return self.password

    @password.setter
    def password(self, plain_text_password):
        self.password_hash = bcrypt.generate_password_hash(plain_text_password).decode('utf-8')

    def check_password_correction(self, attempted_password):
        return bcrypt.check_password_hash(self.password_hash, attempted_password)


def __repr__(self):
    return f'Credentials {self.fname}'
