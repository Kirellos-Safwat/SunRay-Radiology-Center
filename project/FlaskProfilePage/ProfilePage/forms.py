from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField, SelectField, DateField
from wtforms.validators import Length, EqualTo, Email, DataRequired, ValidationError, NumberRange
from ProfilePage.models import Patient, radiologist
from flask_wtf.file import FileField, FileAllowed



class LoginForm(FlaskForm):
    Email = StringField(label='Email:', validators=[Email(), DataRequired()])
    Password = PasswordField(label='Password:', validators=[Length(min=6), DataRequired()])
    submit = SubmitField(label='Sign In')


class PatientEditProfileForm(FlaskForm):
    First_Name = StringField(label='First Name:', validators=[Length(min=2, max=50), DataRequired()])
    Last_Name = StringField(label='Last Name:', validators=[Length(min=2, max=30), DataRequired()])
    Email = StringField(label='Email:', validators=[Email(), DataRequired()])
    Phone_Number = StringField(label='Phone Number:', validators=[Length(min=11, max=13), DataRequired()])
    profile_photo = FileField('Profile Photo', validators=[FileAllowed(['jpg', 'png'])])
    Gender = StringField(label='Gender:', validators=[DataRequired()])
    Age = IntegerField(label='Age:', validators=[NumberRange(min=0, max=120), DataRequired()])
    Address = StringField(label='Address:', validators=[DataRequired()])
    submit = SubmitField(label='Save Changes')

class RadiologistEditProfileForm(FlaskForm):
    Name = StringField(label='Name:', validators=[Length(min=2, max=50), DataRequired()])
    Email = StringField(label='Email:', validators=[Email(), DataRequired()])
    Phone_Number = StringField(label='Phone Number:', validators=[Length(min=11, max=13), DataRequired()])
    profile_photo = FileField('Profile Photo', validators=[FileAllowed(['jpg', 'png'])])
    Gender = StringField(label='Gender:', validators=[DataRequired()])
    Age = IntegerField(label='Age:', validators=[NumberRange(min=0, max=120), DataRequired()])
    Address = StringField(label='Address:', validators=[DataRequired()])
    submit = SubmitField(label='Save Changes')


class AppointmentForm(FlaskForm):
    date = DateField(' Preferred Day', format='%Y-%m-%d', validators=[DataRequired()])
    doctors = SelectField('Preferred Doctor', validators=[DataRequired()], coerce=str)
    devices = SelectField('Examination Type', validators=[DataRequired()], coerce=str)
    submit = SubmitField(label='Book Appointment')


class RadiologistRegisterForm(FlaskForm):
    def validate_Email(self, email_to_check):
        radiologist_email = radiologist.query.filter_by(d_email=email_to_check.data).first()
        if radiologist_email:
            raise ValidationError('This Email has been used before')

    def validate_Phone_Number(self, phone_to_check):
        d_phone = radiologist.query.filter_by(d_phone=phone_to_check.data).first()
        if d_phone:
            raise ValidationError('This Phone number has been used before')

    D_Name = StringField(label='Full Name:', validators=[Length(min=2, max=50), DataRequired()])
    Email = StringField(label='Email:', validators=[Email(), DataRequired()])
    Phone_Number = StringField(label='Phone Number:', validators=[Length(min=11, max=13), DataRequired()])
    Password = PasswordField(label='Password:', validators=[Length(min=6), DataRequired()])
    Password_Confirmation = PasswordField(label='Confirm Password:', validators=[EqualTo('Password'), DataRequired()])
    # photo field
    profile_photo = FileField('Profile Photo', validators=[FileAllowed(['jpg', 'png'])])  # Add this field
    submit = SubmitField(label='Create Account')


class ReportForm(FlaskForm):
    devices = SelectField('Imaging modality', validators=[DataRequired()], coerce=str)
    patients = SelectField('Patient Name', validators=[DataRequired()], coerce=str)
    r_time = DateField('Date of study', format='%Y-%m-%d', validators=[DataRequired()])
    r_scan = FileField('Imaging', validators=[FileAllowed(['jpg', 'png'])])
    r_study_area = StringField('Study area', validators=[DataRequired()])
    radiation_dose = StringField('Radiation dose:', validators=[DataRequired()])
    r_findings = StringField('Findings:', validators=[DataRequired()])
    r_result = StringField('Impressions:', validators=[DataRequired()])
    submit = SubmitField('Submit Report')



class PatientRegisterForm(FlaskForm):
    def validate_Email(self, email_to_check):
        patient_email = Patient.query.filter_by(email=email_to_check.data).first()
        print(patient_email)
        if patient_email:
            raise ValidationError('This Email has been used before')

    def validate_Phone_Number(self, phone_to_check):
        patient_phone = Patient.query.filter_by(phone=phone_to_check.data).first()
        print(patient_phone)
        if patient_phone:
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


'''
class contactForm(FlaskForm):
    Name = StringField(label='Name:', validators=[Length(min=2, max=30), DataRequired()])
    Email = StringField(label='Email:', validators=[Email(), DataRequired()])
    Message = StringField(label='Message:', validators=[Length(min=2, max=200), DataRequired()])
    submit = SubmitField(label='Send Now')
'''

class ForgetForm(FlaskForm):
    email = StringField(label='Email Address:', validators=[Email(), DataRequired()])
    submit = SubmitField(label='Reset Password')


class ResetPasswordForm(FlaskForm):
    new_password = PasswordField(label='Reset Password:', validators=[Length(min=6), DataRequired()])
    confirm_password = PasswordField(label='Confirm Password:', validators=[EqualTo('new_password'), DataRequired()])
    submit = SubmitField(label='Reset Password')
