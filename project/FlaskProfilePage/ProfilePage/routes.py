import psycopg2.extras
from forms import LoginForm, EditProfileForm, RegisterForm, AppointmentForm
from models import Credentials
from flask_login import login_user
from ProfilePage import app, db, connection
from flask import render_template, redirect, url_for, flash, session
from werkzeug.utils import secure_filename
import os
from flask import request


@app.route('/')  # that is the root url of the website
@app.route('/home')
def home_page():
    return render_template('home.html')


@app.route('/profile')
def profile_page():
    data = session.get('user_data')
    if data is None:
        return redirect('/login')
    return render_template('profile.html', data=data)


@app.route('/users')
def users_page():
    data = session.get('user_data')
    if data is None:
        return redirect('/')
    credentials = Credentials.query.all()
    return render_template('users.html', credentials=credentials)


# os.getcwd() might change from devide to device i think , based on your cwd: current working directory

UPLOAD_FOLDER = os.path.join(os.getcwd(), "project", "FlaskProfilePage", "ProfilePage", "static", "uploads")
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


@app.route('/register', methods=['GET', 'POST'])
def registration_page():
    form = RegisterForm()
    if form.validate_on_submit():
        profile_photo = form.profile_photo.data  # Get profile photo data from form
        if profile_photo:  # Check if a photo was uploaded
            # Save the uploaded photo to a folder or storage location
            filename = secure_filename(profile_photo.filename)
            profile_photo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            profile_photo.save(profile_photo_path)

            # Store only the relative path , this should solve the file duplication
            relative_photo_path = os.path.join('uploads', filename)
        else:
            relative_photo_path = None

        user_to_create = Credentials(
            fname=form.First_Name.data,
            lname=form.Last_Name.data,
            email=form.Email.data,
            phone=form.Phone_Number.data,
            is_admin=True if form.Email.data.endswith('@company.com') else False,
            password=form.Password.data,
            profile_picture=relative_photo_path
        )
        db.session.add(user_to_create)
        db.session.commit()
        return redirect(url_for('thanks_page'))
    if form.errors != {}:
        for err_msg in form.errors.values():
            flash(f'There was an error with creating a user: {err_msg}', category='danger')

    return render_template('registration.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login_page():
    form = LoginForm()
    if form.validate_on_submit():
        attempted_email = Credentials.query.filter_by(email=form.Email.data).first()
        if attempted_email and attempted_email.check_password_correction(
                attempted_password=form.Password.data
        ):
            login_user(attempted_email)
            cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cursor.execute('''
                            SELECT *
                            FROM Credentials
                            WHERE email = %s
                            ''', (form.Email.data,))
            user = cursor.fetchone()
            session['user_data'] = dict(user)
            return redirect('/profile')
        else:
            flash('Incorrect Email or password please try again', category='danger')
    return render_template('login.html', form=form)


@app.route('/logout')
def logout():
    session.pop('user_data')
    return redirect('/')


@app.route('/done')
def thanks_page():
    return render_template('thank_you.html')


@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    form = EditProfileForm()
    data = session.get('user_data')

    if request.method == 'POST' and form.validate_on_submit():
        # get the user from the database based on user's uniique ID
        user = Credentials.query.filter_by(id=data['id']).first()

        # Update user information
        user.fname = form.First_Name.data
        user.lname = form.Last_Name.data
        user.email = form.Email.data
        user.phone = form.Phone_Number.data
        user.is_admin = True if form.Email.data.endswith('@company.com') else False

        # Handle profile photo update
        profile_photo = form.profile_photo.data
        if profile_photo:
            filename = secure_filename(profile_photo.filename)
            profile_photo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            profile_photo.save(profile_photo_path)
            relative_photo_path = os.path.join('uploads', filename)
            user.profile_picture = relative_photo_path

        db.session.commit()
        flash('Your profile has been updated successfully! Please login again', category='success')
        return redirect(url_for('login_page'))  # Redirect to login to refresh

    return render_template('edit_profile.html', data=data, form=form)


@app.route('/BookAppointment', methods=['GET', 'POST'])
def appointment_page():
    form = AppointmentForm()
    data = session.get('user_data')
    if request.method == 'POST' and form.validate_on_submit():
        user = Credentials.query.filter_by(id=data['id']).first()

        # Update user information
        user.fname = form.First_Name.data
        user.lname = form.Last_Name.data
        user.email = form.Email.data
        user.phone = form.Phone_Number.data
        db.session.commit()
        flash('Your appointment has been booked successfully!', category='success')
        return redirect(url_for('home_page'))
    return render_template('appointment.html', form=form, data=data)
