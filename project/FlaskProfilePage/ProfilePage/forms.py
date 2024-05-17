from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import Length, EqualTo, Email, DataRequired,ValidationError
from ProfilePage.models import Credentials
from flask_wtf.file import FileField, FileAllowed

class RegisterForm(FlaskForm):
    def validate_Email(self, email_to_check):
        credential_email = Credentials.query.filter_by(email=email_to_check.data).first()
        if credential_email:
            raise ValidationError('This Email has been used before')
    def validate_Phone_Number(self, phone_to_check):
        credential_phone = Credentials.query.filter_by(phone=phone_to_check.data).first()
        if credential_phone:
            raise ValidationError('This Phone number has been used before')

    First_Name = StringField(label='First Name:', validators=[Length(min=2, max=30), DataRequired()])
    Last_Name = StringField(label='Last Name:', validators=[Length(min=2, max=30), DataRequired()])
    Email = StringField(label='Email:', validators=[Email(), DataRequired()])
    Phone_Number = StringField(label='Phone Number:', validators=[Length(min=11, max=13), DataRequired()])
    Password = PasswordField(label='Password:', validators=[Length(min=6), DataRequired()])
    Password_Confirmation = PasswordField(label='Confirm Password:', validators=[EqualTo('Password'), DataRequired()])
    # photo field
    profile_photo = FileField('Profile Photo', validators=[FileAllowed(['jpg', 'png'])])  # Add this field
    submit = SubmitField(label='Create Account')


class LoginForm(FlaskForm):
    Email = StringField(label='Email:', validators=[Email(), DataRequired()])
    Password = PasswordField(label='Password:', validators=[Length(min=6), DataRequired()])
    submit = SubmitField(label='Sign In')


class EditProfileForm(FlaskForm):
    First_Name = StringField(label='First Name:', validators=[Length(min=2, max=30), DataRequired()])
    Last_Name = StringField(label='Last Name:', validators=[Length(min=2, max=30), DataRequired()])
    Email = StringField(label='Email:', validators=[Email(), DataRequired()])
    Phone_Number = StringField(label='Phone Number:', validators=[Length(min=11, max=13), DataRequired()])
    profile_photo = FileField('Profile Photo', validators=[FileAllowed(['jpg', 'png'])])
    Facebook = StringField(label='Facebook:')
    Twitter = StringField(label='Twitter:')
    Instagram = StringField(label='Instagram:')
    LinkedIn = StringField(label='LinkedIn:')
    submit = SubmitField(label='Save Changes')

class AppointmentForm(FlaskForm):
    First_Name = StringField(label='First Name:', validators=[Length(min=2, max=30), DataRequired()])
    Last_Name = StringField(label='Last Name:', validators=[Length(min=2, max=30), DataRequired()])
    Email = StringField(label='Email:', validators=[Email(), DataRequired()])
    Phone_Number = StringField(label='Phone Number:', validators=[Length(min=11, max=13), DataRequired()])
    submit = SubmitField(label='Book Appointment')

