from ProfilePage import db, login_manager
from ProfilePage import bcrypt
from flask_login import UserMixin


@login_manager.user_loader
def load_user(user_id):
    return Patient.query.get(int(user_id))


class Credentials(db.Model, UserMixin):
    id = db.Column(db.Integer(), primary_key=True)
    fname = db.Column(db.String(length=15), nullable=False)
    lname = db.Column(db.String(length=15), nullable=False)
    email = db.Column(db.String(length=30), nullable=False, unique=True)
    phone = db.Column(db.String(length=13), nullable=False, unique=True)
    password = db.Column(db.String(length=60), nullable=False)  # Will be changed later to false
    profile_picture = db.Column(db.String(length=255))
    is_admin = db.Column(db.Boolean(), default=False)
    facebook = db.Column(db.String(length=255))
    twitter = db.Column(db.String(length=255))
    instagram = db.Column(db.String(length=255))
    linkedin = db.Column(db.String(length=255))

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


class radiology_equipment(db.Model, UserMixin):
    device_id = db.Column(db.Integer(), primary_key=True)
    device_name = db.Column(db.String(length=15), nullable=False)
    Commission_Date = db.Column(db.String(length=15), nullable=False)
    Maintenance_Date = db.Column(db.String(length=15), nullable=False)


class appointments(db.Model, UserMixin):
    A_ID = db.Column(db.Integer(), primary_key=True)
    P_ID = db.Column(db.Integer(), db.ForeignKey('patient.P_ID'), nullable=True)
    D_ID = db.Column(db.Integer(), db.ForeignKey('radiologist.D_ID'), nullable=False)
    device_name = db.Column(db.String(length=15), db.ForeignKey('radiology_equipment.device_name'), nullable=False)
    Device_ID = db.Column(db.String(length=15), db.ForeignKey('radiology_equipment.Device_ID'), nullable=False)
    date = db.Column(db.String(length=15), nullable=False)


class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fname = db.Column(db.String(100))
    lname = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    gender = db.Column(db.String(10))
    age = db.Column(db.Integer)
    address = db.Column(db.String(200))
    time = db.Column(db.DateTime)
    password = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)

    profile_picture = db.Column(db.String(200))
    scans = db.Column(db.String(200))


class radiologist(db.Model):
    d_id = db.Column(db.Integer, primary_key=True)
    d_name = db.Column(db.String(100))
    d_phone = db.Column(db.String(20))
    d_gender = db.Column(db.String(10))
    d_age = db.Column(db.Integer)
    d_address = db.Column(db.String(200))
    d_password = db.Column(db.String(100))
    d_email = db.Column(db.String(100), unique=True)

    d_profile_picture = db.Column(db.String(200))

    def __repr__(self):
        return f'Patient {self.p_name}'
