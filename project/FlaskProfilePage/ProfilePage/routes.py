import psycopg2.extras
from datetime import datetime
from google.oauth2 import id_token
from sqlalchemy.testing.plugin.plugin_base import post
from ProfilePage import app, connection, connection_string, mail, flow, GOOGLE_CLIENT_ID
from ProfilePage import app, db, connection, connection_string, mail, bcrypt, flow, GOOGLE_CLIENT_ID
from flask_login import current_user
from flask_mail import Message
from ProfilePage.models import Patient
from ProfilePage.forms import LoginForm, EditProfileForm, AppointmentForm, PatientRegisterForm, ReportForm, ForgetForm, \
    ResetPasswordForm
from flask import render_template, redirect, url_for, flash, session, request, g
from ProfilePage.models import appointments, Patient
from ProfilePage.forms import LoginForm, EditProfileForm, AppointmentForm, PatientRegisterForm, ReportForm, \
    RadiologistRegisterForm, ForgetForm, \
    ResetPasswordForm
from flask import render_template, redirect, url_for, flash, session, request, json, jsonify
from werkzeug.utils import secure_filename
import os, psycopg2.extras, random
import requests
from google.oauth2 import id_token
from pip._vendor import cachecontrol
import google.auth.transport.requests
# import tensorflow as tf
# from tensorflow import keras
# from keras.models import load_model
# from PIL import Image
# from keras.src.optimizers import Adamax

# model = tf.keras.models.load_model(
#     r"C:\Users\Egypt_Laptop\Desktop\database final project\his-finalproject-database_sbe_spring24_team6\project\FlaskProfilePage\ProfilePage\brain_tumor_v2.h5",
#     compile=False)
# model.compile(Adamax(learning_rate=0.001), loss='categorical_crossentropy', metrics=['accuracy'])


@app.before_request
def load_user_data():
    g.data = session.get('user_data')  # Use Flask's global `g` object


@app.route('/')  # that is the root url of the website
@app.route('/home')
def home_page():
    print(g.data)
    cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute('''
            SELECT id, name, picture
            FROM(
                SELECT rad.d_id AS id, rad.d_name AS name,rad.d_profile_picture AS picture, SUM(billing) AS toal_billing
                FROM radiologist AS rad JOIN report AS rep ON rad.d_id = rep.d_id
                GROUP BY rad.d_id, d_name, d_profile_picture
                ORDER BY toal_billing DESC
                LIMIT 3);
            ''')
    special_doctors = cursor.fetchall()
    cursor.close()
    return render_template('home.html', data=g.data, template='home', special_doctors=special_doctors)


@app.route('/edit_data', methods=['POST'])
def edit_data():
    data = request.get_json()
    table = data.get('table')
    cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
    # handle deleting
    if 'delete_id' in data:
        delete_id = data['delete_id']
        if table == 'patient':
            update_query = """
                DELETE FROM patient 
                WHERE id = %s;
            """
        if table == 'doctor':
            update_query = """
                DELETE FROM radiologist 
                WHERE d_id = %s;
            """
        cursor.execute(update_query, (str(delete_id),))
    # handle editing
    elif 'new' in data:
        doctor_data = {
            'd_name': data['d_name'],
            'd_phone': data['d_phone'],
            'd_email': data['d_email']
        }
        add_query = """
            INSERT INTO radiologist(d_name, d_email, d_phone)
            VALUES(%(d_name)s, %(d_email)s, %(d_phone)s)
        """
        cursor.execute(add_query, doctor_data)
    # adding new doctor
    elif 'id' in data or 'd_id' in data:
        update_data = data
        if table == 'patient':
            update_query = f"""
                UPDATE patient SET 
                {', '.join(
                f"{key} = '{value}'"
                for key, value in update_data.items()
                if key != 'id' and key != 'table')}
                WHERE id = {update_data['id']};
            """
        if table == 'doctor':
            update_query = f"""
                UPDATE radiologist SET 
                {', '.join(
                f"{key} = '{value}'"
                for key, value in update_data.items()
                if key != 'id' and key != 'table')}
                WHERE d_id = {update_data['id']};
            """
        cursor.execute(update_query, update_data)
    cursor.close()
    connection.commit()
    return redirect(url_for('users_page'))


@app.route('/BookAppointment', methods=['GET', 'POST'])
def appointment_page():
    form = AppointmentForm()
    if g.data is None or 'id' not in g.data:
        return redirect(url_for('patient_login_page'))

    def get_doctors():
        connection = psycopg2.connect(connection_string)
        curs = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
        curs.execute("SELECT d_name FROM radiologist")
        doctors = curs.fetchall()
        curs.execute("ROLLBACK")
        connection.commit()
        curs.close()
        # connection.close()
        return [doctor['d_name'] for doctor in doctors]

    def get_devices():
        connection = psycopg2.connect(connection_string)
        curs = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
        curs.execute("SELECT device_name,device_id FROM radiology_equipment")
        devices = curs.fetchall()
        curs.execute("ROLLBACK")
        connection.commit()
        curs.close()
        # connection.close()
        return [device['device_name'] for device in devices]

    form.doctors.choices = get_doctors()
    form.devices.choices = get_devices()

    if request.method == 'POST':
        connection = psycopg2.connect(connection_string)
        cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
        p_id = g.data['id']
        if form.validate_on_submit():
            date = form.date.data
            d_name = form.doctors.data
            cursor.execute("SELECT d_id FROM radiologist WHERE d_name = %s", (d_name,))
            d_id = cursor.fetchall()[0][0]
            cursor.execute("ROLLBACK")
            device_name = form.devices.data
            cursor.execute("SELECT device_id FROM radiology_equipment WHERE device_name = %s",
                           (device_name,))
            device_id = cursor.fetchall()[0][0]
            cursor.execute("ROLLBACK")

            cursor.execute(
                "INSERT INTO appointments (d_id,device_name,device_id,date,d_name,p_id) VALUES (%s, %s, %s, %s,%s,%s)",
                (d_id, device_name, device_id, date, d_name, p_id)
            )
            connection.commit()
            cursor.close()
            # connection.close()
            flash('Your appointment has been booked successfully!', category='success')
            return redirect(url_for('patient_profile_page'))
    return render_template('appointment.html', form=form, data=g.data)


@app.route('/SubmitReport', methods=['GET', 'POST'])
def report_page():
    form = ReportForm()
    if g.data is None or 'd_id' not in g.data:
        return redirect(url_for('radiologist_login'))

    def get_patients():
        connection = psycopg2.connect(connection_string)
        curs = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
        curs.execute("SELECT concat(fname,' ',lname) AS full_name FROM patient")
        patients = curs.fetchall()
        connection.close()
        return [(patient['full_name'], patient['full_name']) for patient in patients]

    def get_devices():
        connection = psycopg2.connect(connection_string)
        curs = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
        curs.execute("SELECT device_name FROM radiology_equipment")
        devices = curs.fetchall()
        connection.close()
        return [(device['device_name'], device['device_name']) for device in devices]

    form.patients.choices = get_patients()
    form.devices.choices = get_devices()

    if request.method == 'POST':
        if form.validate_on_submit():
            connection = psycopg2.connect(connection_string)
            cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
            d_id = g.data['d_id']

            r_time = form.r_time.data
            r_study_area = form.r_study_area.data
            radiation_dose = form.radiation_dose.data
            r_findings = form.r_findings.data
            r_result = form.r_result.data
            billing = random.randint(500, 1000)

            profile_photo = form.r_scan.data

            filename = secure_filename(profile_photo.filename)
            profile_photo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            profile_photo.save(profile_photo_path)
            relative_photo_path = os.path.join('uploads', filename)



            p_name = form.patients.data

            cursor.execute("SELECT id FROM patient WHERE concat(fname,' ',lname) = %s", (p_name,))
            p_id = cursor.fetchone()[0]

            device_name = form.devices.data
            cursor.execute("SELECT device_id FROM radiology_equipment WHERE device_name = %s", (device_name,))
            device_id = cursor.fetchone()[0]

            cursor.execute(
                "INSERT INTO report (p_id, d_id, device_id, r_time, r_scan, r_study_area, radiation_dose, r_findings, r_result, billing) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (p_id, d_id, device_id, r_time, relative_photo_path, r_study_area, radiation_dose, r_findings, r_result, billing)
            )
            connection.commit()
            cursor.close()
            # connection.close()

            flash('The report was submitted successfully', category='success')
            return redirect(url_for('radiologist_profile_page'))
    return render_template('report.html', form=form, data=g.data)


@app.route('/login', methods=['GET', 'POST'])
def login_admin():
    if request.method == 'POST':
        email = request.form['Email']
        password = request.form['Password']
        cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute(
            "SELECT * FROM admin WHERE a_email = %s AND password = %s",
            (email, password)
        )
        user = cursor.fetchone()

        if user:
            session['user_data'] = dict(user)
            data = session['user_data']
            cursor.close()  # Close the cursor once
            return redirect('/users')
        else:
            flash('Incorrect Email or password. Please try again.', category='error')

    return render_template('admin_login.html', form=LoginForm(), data=data if 'data' in locals() else None)


@app.route('/users')
def users_page():
    data = session.get('user_data')
    if data is None or 'admin_id' not in data:
        return redirect('/login')
    cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
    # patients data
    cursor.execute('SELECT * FROM patient')
    patients = cursor.fetchall()
    # doctors data
    cursor.execute('SELECT * FROM radiologist')
    doctors = cursor.fetchall()
    # devices data1x
    cursor.execute('SELECT * FROM radiology_equipment')
    devices = cursor.fetchall()

    cursor.close()
    return render_template('users.html', patients=patients, doctors=doctors, devices=devices, data=g.data, template='users')



@app.route('/logout')
def logout():
    session.pop('user_data')
    try:
        session.pop('update')
    except:
        pass
    return redirect('/')


@app.route('/radiologist-login', methods=['GET', 'POST'])
def radiologist_login():
    if request.method == 'POST':
        d_email = request.form['Email']
        d_password = request.form['Password']
        cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute(
            "SELECT * FROM radiologist WHERE d_email = %s AND d_password = %s",
            (d_email, d_password)
        )
        user = cursor.fetchone()

        if user:
            session['user_data'] = dict(user)
            data = session['user_data']
            if os.name == 'nt' and data['d_profile_picture'] is not None:
                data['profile_picture'] = data['d_profile_picture'].replace("\\", "/")
            cursor.close()  # Close the cursor once
            return redirect('/radiologist-profile')
        else:
            flash('Incorrect Email or password. Please try again.', category='error')

    return render_template('radiologist-login.html', form=LoginForm(), data=data if 'data' in locals() else None) #


@app.route('/radiologist-profile')
def radiologist_profile_page():
    if g.data is None or 'd_id' not in g.data:
        return redirect('/radiologist-login')
    cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
    # Fetch appointments for the current user's ID
    cursor.execute("""
            SELECT appointments.*, patient.fname, patient.lname
            FROM appointments
            JOIN patient ON appointments.p_id = Patient.id
            WHERE appointments.d_id = %s
        """, (g.data['d_id'],))
    appointments = cursor.fetchall()
    cursor.close()

    cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
    # Fetch reports for the current user's ID
    cursor.execute(""" SELECT report.*, patient.fname, patient.lname
                   FROM report Join patient ON report.p_id = patient.id
                   WHERE d_id = %s """, (g.data['d_id'],))
    reports = cursor.fetchall()
    cursor.close()

    if g.data is None:
        return redirect('/radiologist-login')
    return render_template('radiologist-profile.html', data=g.data, appointments=appointments , template = 'radiologist_profile',reports=reports)


@app.route('/radiologist-edit_profile', methods=['GET', 'POST'])
def radiologist_edit_profile():
    form = EditProfileForm()
    if g.data is None or 'd_id' not in g.data:
        return redirect('/radiologist-login')
    if request.method == 'POST' and form.validate_on_submit():
        updated_data = {
            'd_name': form.First_Name.data,
            'd_email': form.Email.data,
            'd_phone': form.Phone_Number.data,
            'd_gender': form.Gender.data,
            'd_age': form.Age.data,
            'd_address': form.Address.data,
            'd_is_admin': True if form.Email.data.endswith('@company.com') else False,

        }

        profile_photo = form.profile_photo.data

        if profile_photo:
            filename = secure_filename(profile_photo.filename)
            profile_photo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            profile_photo.save(profile_photo_path)
            relative_photo_path = os.path.join('uploads', filename)
            updated_data['profile_picture'] = relative_photo_path
        else:
            updated_data['profile_picture'] = g.data['profile_picture']

        # Update user information in the database
        connection = psycopg2.connect(connection_string)
        cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
        update_query = """
            UPDATE radiologist
            SET d_name = %(d_name)s, d_email = %(d_email)s,
                d_phone = %(d_phone)s, d_gender = %(d_gender)s, d_age = %(d_age)s, d_address = %(d_address)s,
                d_profile_picture = %(d_profile_picture)s
            WHERE d_id = %(d_id)s;
        """
        updated_data['d_id'] = g.data['d_id']

        cursor.execute(update_query, updated_data)
        connection.commit()
        cursor.close()
        # connection.close()

        flash('Your profile has been updated successfully! Please login again', category='success')
        return redirect('/radiologist-login_page')  # Redirect to log in to refresh

    return render_template('radiologist_edit_profile.html', data=g.data, form=form, template = 'radiologist_edit_profile')


#######################################################################
@app.route('/patient-register', methods=['GET', 'POST'])
def patient_registration_page():
    form = PatientRegisterForm()
    if form.validate_on_submit():
        fname = form.First_Name.data
        lname = form.Last_Name.data
        email = form.Email.data
        phone = form.Phone_Number.data
        password = form.Password.data

        profile_photo = form.profile_photo.data
        if profile_photo:
            filename = secure_filename(profile_photo.filename)
            profile_photo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            profile_photo.save(profile_photo_path)
            relative_photo_path = os.path.join('uploads', filename)
        else:
            relative_photo_path = None

        connection = psycopg2.connect(connection_string)
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO Patient (fname, lname, email, phone, password, profile_picture) VALUES (%s, %s, %s, %s, %s, %s)",
            (fname, lname, email, phone, password, relative_photo_path)
        )
        connection.commit()
        cursor.close()
        # connection.close()

        flash('Registration successful. Please log in.', category='success')
        return redirect('/patient-login_page')

    return render_template('patient_registration.html', form=form, data=None)


@app.route('/patient-login_page', methods=['GET', 'POST'])
def patient_login_page():
    if request.method == 'POST':
        email = request.form['Email']
        password = request.form['Password']
        cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute(
            "SELECT * FROM patient WHERE email = %s AND password = %s",
            (email, password)
        )
        user = cursor.fetchone()

        if user:
            session['user_data'] = dict(user)
            data = session['user_data']
            if os.name == 'nt' and data['scans'] is not None:
                data['scans'] = data['scans'].replace("\\", "/")
            if os.name == 'nt' and data['profile_picture'] is not None:
                data['profile_picture'] = data['profile_picture'].replace("\\", "/")
            cursor.close()  # Close the cursor once
            flash('Welcome back!', category='success')
            return redirect('/patient-profile')
        else:
            flash('Incorrect Email or password. Please try again.', category='error')

    return render_template('patient-login.html', form=LoginForm(), data=data if 'data' in locals() else None)


@app.route('/patient-profile')
def patient_profile_page():
    if g.data is None or 'id' not in g.data:
        return redirect('/patient-login_page')
    cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
    # Fetch appointments for the current user's ID
    cursor.execute("""
        SELECT appointments.*, radiologist.d_name
        FROM appointments
        JOIN radiologist ON appointments.D_ID = radiologist.d_id
        WHERE P_ID = %s
    """, (g.data['id'],))
    appointments = cursor.fetchall()
    cursor.close()

    ############################################
    scans_folder = "patient" + str(g.data['id'])  # make a folder for each patient
    scans_path = os.path.join(app.config['UPLOAD_FOLDER'], scans_folder)
    if os.path.exists(scans_path):
        scan_Files = os.listdir(scans_path)  # must be absolute path
    else:
        scan_Files = []
    ############################################
    # if os.name == 'nt' and data['scans'] is not None:
    #     data['scans'] = data['scans'].replace("\\", "/")
    cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
    # Fetch reports for the current user's ID
    cursor.execute(""" SELECT report.*, patient.fname, patient.lname
                   FROM report Join patient ON report.p_id = patient.id
                   WHERE id = %s """, (g.data['id'],))
    reports = cursor.fetchall()
    cursor.close()
    if g.data is None:
        return redirect('/patient-login')
    return render_template('patient-profile.html', data=g.data, scan_Files=scan_Files, appointments=appointments, reports=reports)


@app.route('/upload_scan', methods=['GET', 'POST'])
def patient_upload_scan():
    if g.data is None or 'id' not in g.data:
        return redirect('/patient-login_page')
    scans_folder = "patient" + str(g.data['id'])  # make a folder for each patient
    scans_path = os.path.join(app.config['UPLOAD_FOLDER'], scans_folder)
    if g.data is None:
        return redirect('/patient-login')

    if not os.path.exists(scans_path):
        os.makedirs(scans_path)
    else:
        scan_files = os.listdir(scans_path)

    if request.method == 'POST':
        scan_file = request.files['scan_file']
        if scan_file and scan_file.filename != '':
            filename = secure_filename(scan_file.filename)
            scan_file_path = os.path.join(scans_path, filename)
            scan_file.save(scan_file_path)
            flash('Scan uploaded successfully!', category='success')
        else:
            flash('No scan file selected!', category='error')

    scan_files = []  # this list stores paths to the scan files
    if os.path.exists(scans_path):
        scan_files = os.listdir(scans_path)
    relative_scan_folder = os.path.join('uploads', scans_folder)
    cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute(
        "UPDATE patient SET scans = %s WHERE id = %s",
        (relative_scan_folder, g.data['id'])
    )  # insert to the specific patient
    connection.commit()
    cursor.close()

    return render_template('upload_scan.html', data=g.data, scan_files=scan_files)


@app.route('/patient-edit_profile', methods=['GET', 'POST'])
def patient_edit_profile():
    form = EditProfileForm()
    if g.data is None or 'id' not in g.data:
        return redirect('/patient-login_page')
    if request.method == 'POST' and form.validate_on_submit():
        updated_data = {
            'fname': form.First_Name.data,
            'lname': form.Last_Name.data,
            'email': form.Email.data,
            'phone': form.Phone_Number.data,
            'gender': form.Gender.data,
            'age': form.Age.data,
            'address': form.Address.data,
            'is_admin': True if form.Email.data.endswith('@company.com') else False,

        }

        profile_photo = form.profile_photo.data

        if profile_photo:
            filename = secure_filename(profile_photo.filename)
            profile_photo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            profile_photo.save(profile_photo_path)
            relative_photo_path = os.path.join('uploads', filename)
            updated_data['profile_picture'] = relative_photo_path
        else:
            updated_data['profile_picture'] = g.data['profile_picture']

        # Update user information in the database
        connection = psycopg2.connect(connection_string)
        cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
        update_query = """
            UPDATE patient
            SET fname = %(fname)s, lname = %(lname)s, email = %(email)s,
                phone = %(phone)s, gender = %(gender)s, age = %(age)s, address = %(address)s,
                profile_picture = %(profile_picture)s
            WHERE id = %(id)s;
        """
        updated_data['id'] = g.data['id']

        cursor.execute(update_query, updated_data)
        connection.commit()
        cursor.close()
        # connection.close()

        flash('Your profile has been updated successfully! Please login again', category='success')
        return redirect('/patient-login_page')  # Redirect to log in to refresh

    return render_template('patient_edit_profile.html', data=g.data, form=form)


@app.route('/contactUs', methods=['GET', 'POST'])
def contact_page():
    if request.method == 'POST':
        flash('We have received your message. Thank you for contacting us', category='success')
        return redirect('/home')
    '''
        form = contactForm()
        if request.method == 'POST':
        name = request.form.get('Name')
        email = request.form.get('Email')
        message = request.form.get('Message')

        msg = Message(
            subject=f"Mail from {name}",  body=f"Name: {name}\nEmail: {email}\n\n\n{message}", sender="rawanwalid978", recipients="rawanwalid978@gmial.com"
        )
        mail.send(msg)

        connection = psycopg2.connect(connection_string)
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO Patient (Message) VALUES (%s)",
            (message)
        )
        connection.commit()
        cursor.close()
        connection.close()
    '''
    return render_template('contact.html', data= g.data)



def send_reset_email(patient):
    token = patient.get_reset_token()
    msg = Message('Password Reset Request',
                  sender='noreply@demo.com',
                  recipients=[patient.email])
    msg.body = f'''To reset your password, visit the following link:
{url_for('reset_token', token=token, _external=True)}

If you did not make this request then simply ignore this email and no changes will be made.
'''
    mail.send(msg)


@app.route('/forgetPassword', methods=('GET', 'POST'))
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = ForgetForm()
    if form.validate_on_submit():
        patient = Patient.query.filter_by(email=form.email.data).first()
        send_reset_email(patient)
        flash('An email has been sent with instructions to reset your password.', 'info')
        return redirect(url_for('patient_login_page'))
    return render_template("forgetPassword.html", form=form, data=None)


@app.route("/forgetPassword/<token>", methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    '''
    patient = Patient.verify_reset_token(token)
    if patient is None:
        flash('That is an invalid or expired token', category='warning')
        return redirect(url_for('reset_request'))
    '''
    form = ResetPasswordForm()
    if request.method == 'POST' and form.validate_on_submit():
        updated_data = {
            'password': form.new_password.data,
        }
        # Update user information in the database
        connection = psycopg2.connect(connection_string)
        cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
        update_query = """
            UPDATE patient
            SET password = %(password)s
            WHERE id = %(id)s;
        """
        updated_data['id'] = g.data['id']

        cursor.execute(update_query, updated_data)
        connection.commit()
        cursor.close()
        # connection.close()

        flash('Your password has been updated successfully! You are now able to log in', category='success')
        return redirect('/patient-login_page')  # Redirect to log in to refresh
    return render_template("ResetPassword.html", form=form, data=None)


def login_is_required(function):
    def wrapper(*args, **kwargs):
        if "google_id" not in session:
            return os.abort(401)  # Authorization required
        else:
            return function()

    return wrapper


@app.route("/googleLogin")
def google_login():
    authorization_url, state = flow.authorization_url()
    session["state"] = state
    return redirect(authorization_url)


@app.route("/callback")
def callback():
    flow.fetch_token(authorization_response=request.url)

    if not session["state"] == request.args["state"]:
        os.abort(500)  # State does not match!

    credentials = flow.credentials
    request_session = requests.session()
    cached_session = cachecontrol.CacheControl(request_session)
    token_request = google.auth.transport.requests.Request(session=cached_session)

    id_info = id_token.verify_oauth2_token(
        id_token=credentials._id_token,
        request=token_request,
        audience=GOOGLE_CLIENT_ID
    )
    session["google_id"] = id_info.get("sub")
    session["name"] = id_info.get("name")

    email = id_info.get("email")
    full_name = id_info.get("name")
    name_parts = full_name.split(" ", 1)
    first_name = name_parts[0] if len(name_parts) >= 1 else ""
    last_name = name_parts[1] if len(name_parts) >= 2 else ""
    if email:
        # Check user existence
        user = Patient.query.filter_by(email=email).first()
        if not user:
            # Create new user with Google information
            connection = psycopg2.connect(connection_string)
            cursor = connection.cursor()
            cursor.execute(
                "INSERT INTO Patient (fname, lname, email) VALUES (%s, %s, %s) RETURNING id",
                (first_name, last_name, email)
            )
            # Fetch the returned data (assuming only one new user was inserted)
            new_user = cursor.fetchone()
            connection.commit()
            cursor.close()
            # connection.close()
            user_data = {
                "id": new_user[0],
                "email": email,
                "fname": first_name,
                "lname": last_name,
            }
            session["user_data"] = user_data
        else:
            user_data = {
                "id": user.id,
                "email": user.email,
                "fname": user.fname,  # Assuming your model has attributes fname and lname
                "lname": user.lname,
            }
            session["user_data"] = user_data
        return redirect("/patient-profile")
    else:
        print("Email not found in Google ID token. User creation skipped.")
    return redirect("/home")



@app.route('/predict', methods=['GET', 'POST'])
def predict():
    if request.method == 'POST':
        image_file = request.files['imagefile']
        image_path = r"C:\Users\Egypt_Laptop\Desktop\database final project\his-finalproject-database_sbe_spring24_team6\project\FlaskProfilePage\ProfilePage\images" + image_file.filename
        image_file.save(image_path)
        img = image.load_img(image_path)
        img_array = image.img_to_array(img)
        img_array = tf.image.resize(img_array, [224, 244])
        img_array = tf.keras.applications.efficientnet.preprocess_input(img_array)
        img_array = tf.expand_dims(img_array, axis=0)
        # Make prediction
        prediction = model.predict(img_array)
        class_labels = ['glioma', 'meningioma', 'notumor', 'pituitary']
        # Return prediction result
        score = tf.nn.softmax(prediction[0])
        result = class_labels[tf.argmax(score)]
        return render_template("result.html", result=result)
    else:
        return render_template('index.html')


@app.route("/dashboard")
def dashboard():
    connection = psycopg2.connect(connection_string)
    # most crowded day
    def appointments_per_day():
        cursor = connection.cursor()
        cursor.execute("SELECT date FROM appointments")
        dates = cursor.fetchall()
        cursor.close()
        days = []
        for date in dates:
            days.append(datetime.strptime(date[0], "%Y-%m-%d").strftime("%A"))
        appointments_per_day = {
            'Monday': days.count('Monday'),
            'Tuesday': days.count('Tuesday'),
            'Wednesday': days.count('Wednesday'),
            'Thursday': days.count('Thursday'),
            'Friday': days.count('Friday'),
            'Saturday': days.count('Saturday'),
            'Sunday': days.count('Sunday')
        }
        return appointments_per_day

    # age/gender demographics
    def demographics():
        cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute('''
        SELECT males FROM (SELECT CASE 
        WHEN age BETWEEN 0 AND 18 THEN '0-18'
        WHEN age BETWEEN 19 AND 30 THEN '19-30'
        WHEN age BETWEEN 31 AND 45 THEN '31-45'
        WHEN age BETWEEN 46 AND 60 THEN '46-60'
        WHEN age > 60 THEN '60+' END AS age_groups, 
        gender, COUNT(*) AS males
        FROM patient
        WHERE gender = 'M'
        GROUP BY age_groups, gender
        ORDER BY age_groups);
        ''')
        males = cursor.fetchall()
        cursor.execute('''
        SELECT males FROM (SELECT CASE 
        WHEN age BETWEEN 0 AND 18 THEN '0-18'
        WHEN age BETWEEN 19 AND 30 THEN '19-30'
        WHEN age BETWEEN 31 AND 45 THEN '31-45'
        WHEN age BETWEEN 46 AND 60 THEN '46-60'
        WHEN age > 60 THEN '60+' END AS age_groups, 
        gender, COUNT(*) AS males
        FROM patient
        WHERE gender = 'F'
        GROUP BY age_groups, gender
        ORDER BY age_groups);
        ''')
        females = cursor.fetchall()
        cursor.close()
        demographics_data = {
            'age_groups': ['0-18', '19-30', '31-45', '46-60', '60+'],
            'male': [i[0] for i in males],
            'female': [i[0] for i in females]
        }
        return demographics_data

    # most served age group
    def most_served_age_group():
        cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute('''
        SELECT CASE 
        WHEN age BETWEEN 0 AND 18 THEN '0-18'
        WHEN age BETWEEN 19 AND 30 THEN '19-30'
        WHEN age BETWEEN 31 AND 45 THEN '31-45'
        WHEN age BETWEEN 46 AND 60 THEN '46-60'
        WHEN age > 60 THEN '60+' END AS age_groups, COUNT(*) AS count
        FROM patient
        GROUP BY age_groups
        ORDER BY count DESC
        LIMIT 1;
        ''')
        age_group = cursor.fetchone()
        cursor.close()
        return age_group

    # most contributing doctor
    def doctors_data():
        cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute('''
        SELECT rad.d_id, d_name, SUM(billing) AS toal_billing, COUNT(*) AS appointments
        FROM radiologist AS rad JOIN report AS rep ON rad.d_id = rep.d_id
        GROUP BY rad.d_id, d_name, d_profile_picture
        ORDER BY toal_billing DESC;
        ''')
        doctors_data = cursor.fetchall()
        cursor.close()
        return doctors_data

    # total number of patients, doctors, equipments
    def total_patients_docotrs_equipments():
        cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute('''
        SELECT COUNT(id) FROM patient
        ''')
        total_patients = cursor.fetchone()
        cursor.execute('''
        SELECT COUNT(d_id) FROM radiologist
        ''')
        total_doctors = cursor.fetchone()
        cursor.execute('''
        SELECT COUNT(device_id) FROM radiology_equipment
        ''')
        total_equipments = cursor.fetchone()
        cursor.close()
        return (total_patients, total_doctors, total_equipments)

    # total revenues last month and last year
    def total_revenues_last_month_last_year():
        cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
        current_month = datetime.today().month
        year = datetime.today().year
        last_month = current_month - 1 if current_month > 1 else 12
        last_month = str('0'+str(last_month)) if last_month < 10 else str(last_month)
        last_month_year = str(year) if current_month > 1 else str(year - 1)
        cursor.execute(f'''
        SELECT SUM(billing) 
        FROM report
        WHERE r_time LIKE '{last_month_year}-{last_month}-%'
        ''')
        last_month = cursor.fetchone()
        cursor.execute(f'''
        SELECT SUM(billing) 
        FROM report
        WHERE r_time LIKE '{year - 1}%'
        ''')
        last_year = cursor.fetchone()
        cursor.close()
        return (last_month, last_year)

    # upcoming maintenances
    def upcoming_maintenances():
        cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
        print(datetime.today().strftime('%d/%m/%Y'))
        # cursor.execute(f'''
        # SELECT device_id, device_name, maintenance_date
        # FROM radiology_equipment
        # WHERE TO_DATE(maintenance_date, '%d/%m/%Y') > TO_DATE({datetime.today().strftime('%d/%m/%Y')}, '%d/%m/%Y');
        # ''')
        # upcoming_maintenances = cursor.fetchall()
        return None
    print(upcoming_maintenances())
    return render_template('dashboard.html', days=appointments_per_day(), data= g.data,
        most_crowded_day=max(appointments_per_day(), key=appointments_per_day().get), demographics=demographics(),
        most_served_age_group=most_served_age_group(), doctors_data=doctors_data(),
        total_patients_docotrs_equipments=total_patients_docotrs_equipments(), total_revenues_last_month_last_year=total_revenues_last_month_last_year())