import psycopg2.extras
import random
from ProfilePage.forms import RegisterForm, LoginForm, EditProfileForm, AppointmentForm, PatientRegisterForm, ReportForm
from ProfilePage import app, db, connection, connection_string
from flask import render_template, redirect, url_for, flash, session
from werkzeug.utils import secure_filename
import os
from flask import request

from ProfilePage.models import appointments


@app.route('/')  # that is the root url of the website
@app.route('/home')
def home_page():
    return render_template('home.html')


UPLOAD_FOLDER = os.path.join(os.getcwd(), "project", "FlaskProfilePage", "ProfilePage", "static", "uploads")
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


@app.route('/BookAppointment', methods=['GET', 'POST'])
def appointment_page():
    form = AppointmentForm()
    data = session.get('user_data')  # This should be changed to get the patient data from the database

    def get_doctors():
        connection = psycopg2.connect(connection_string)
        curs = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
        curs.execute("SELECT d_name FROM radiologist")
        doctors = curs.fetchall()
        curs.execute("ROLLBACK")
        connection.commit()
        curs.close()
        connection.close()
        return [doctor['d_name'] for doctor in doctors]

    def get_devices():
        connection = psycopg2.connect(connection_string)
        curs = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
        curs.execute("SELECT device_name,device_id FROM radiology_equipment")
        devices = curs.fetchall()
        curs.execute("ROLLBACK")
        connection.commit()
        curs.close()
        connection.close()
        return [device['device_name'] for device in devices]

    form.doctors.choices = get_doctors()
    form.devices.choices = get_devices()

    if request.method == 'POST':
        connection = psycopg2.connect(connection_string)
        cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
        p_id = data['id']
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
            connection.close()

            flash('Your appointment has been booked successfully!', category='success')
            return redirect(url_for('home_page'))
    return render_template('appointment.html', form=form, data=data)


@app.route('/SubmitReport', methods=['GET', 'POST'])
def report_page():
    form = ReportForm()
    data = session.get('user_data')  # This should be changed to get the patient data from the database

    def get_patients():
        connection = psycopg2.connect(connection_string)
        curs = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
        curs.execute("select concat(fname,' ',lname) AS full_name FROM patient")
        patients = curs.fetchall()
        curs.execute("ROLLBACK")
        connection.commit()
        curs.close()
        connection.close()
        return [patient['full_name'] for patient in patients]

    def get_devices():
        connection = psycopg2.connect(connection_string)
        curs = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
        curs.execute("SELECT device_name,device_id FROM radiology_equipment")
        devices = curs.fetchall()
        curs.execute("ROLLBACK")
        connection.commit()
        curs.close()
        connection.close()
        return [device['device_name'] for device in devices]

    form.patients.choices = get_patients()
    form.devices.choices = get_devices()

    if request.method == 'POST':
        connection = psycopg2.connect(connection_string)
        cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
        d_id = None

        if form.validate_on_submit():
            r_time = form.r_time.data
            r_scan = form.r_scan.data
            r_study_area = form.r_study_area.data
            radiation_dose = form.radiation_dose.data
            r_findings = form.r_findings.data
            r_result = form.r_result.data
            billing = random.randint(500, 1000)

            p_name = form.patients.data
            cursor.execute("SELECT id FROM patient WHERE concat(fname,' ',lname) = %s", (p_name,))
            p_id = cursor.fetchall()[0][0]
            cursor.execute("ROLLBACK")
            device_name = form.devices.data
            cursor.execute("SELECT device_id FROM radiology_equipment WHERE device_name = %s",
                           (device_name,))
            device_id = cursor.fetchall()[0][0]
            cursor.execute("ROLLBACK")

            cursor.execute(
                "INSERT INTO report (p_id,d_id,device_id,r_time,r_scan,r_study_area,radiation_dose,r_findings,r_result,billing) VALUES (%s, %s, %s, %s,%s,%s, %s, %s, %s,%s)",
                (p_id, d_id, device_id, r_time, r_scan, r_study_area, radiation_dose, r_findings, r_result, billing)
            )
            connection.commit()
            cursor.close()
            connection.close()

            flash('The report was submitted successfully', category='success')
            return redirect(url_for('report_page'))
    return render_template('report.html', form=form, data=data)


@app.route('/register', methods=['GET', 'POST'])
def registration_page():
    form = RegisterForm()
    if request.method == 'POST':
        fname = request.form['First_Name']
        lname = request.form['Last_Name']
        email = request.form['Email']
        phone = request.form['Phone_Number']
        password = request.form['Password']
        is_admin = True if email.endswith('@company.com') else False

        profile_photo = request.files['profile_photo']
        if profile_photo and profile_photo.filename != '':
            filename = secure_filename(profile_photo.filename)
            profile_photo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            profile_photo.save(profile_photo_path)
            relative_photo_path = os.path.join('uploads', filename)
        else:
            relative_photo_path = None
        connection = psycopg2.connect(connection_string)
        cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
        if form.validate_on_submit():
            cursor.execute(
                "INSERT INTO Credentials (fname, lname, email, phone, password, profile_picture ,is_admin) VALUES (%s, %s, %s, %s, %s, %s , %s)",
                (fname, lname, email, phone, password, relative_photo_path, is_admin)

            )
            connection.commit()
            cursor.close()
            connection.close()
            flash('Registration successful. Please log in.', category='success')
            return redirect(url_for('login_page'))
        else:
            flash('Invalid email or password. Please try again.', category='danger')

    return render_template('registration.html', form=RegisterForm())


@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        email = request.form['Email']
        password = request.form['Password']
        cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute(
            "SELECT * FROM Credentials WHERE email = %s AND password = %s",
            (email, password)
        )
        user = cursor.fetchone()

        if user:
            session['user_data'] = dict(user)
            cursor.close()  # Close the cursor once
            return redirect('/profile')
        else:
            flash('Incorrect Email or password. Please try again.', category='danger')

    return render_template('login.html', form=LoginForm())


@app.route('/profile')
def profile_page():
    data = session.get('user_data')
    if data is None:
        return redirect('/login')
    if os.name == 'nt' and data['profile_picture'] != None:
        data['profile_picture'] = data['profile_picture'].replace("\\", "/")
        print(data['profile_picture'])
    return render_template('profile.html', data=data)


@app.route('/users')
def users_page():
    data = session.get('user_data')
    if data is None:
        return redirect('/')
    cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute('SELECT * FROM Credentials')

    # Fetch all the results
    credentials = cursor.fetchall()
    cursor.close()
    return render_template('users.html', credentials=credentials)


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
        updated_data = {
            'fname': form.First_Name.data,
            'lname': form.Last_Name.data,
            'email': form.Email.data,
            'phone': form.Phone_Number.data,
            'is_admin': True if form.Email.data.endswith('@company.com') else False,
            'facebook': form.Facebook.data,
            'twitter': form.Twitter.data,
            'instagram': form.Instagram.data,
            'linkedin': form.LinkedIn.data,
        }

        profile_photo = form.profile_photo.data

        if profile_photo:
            filename = secure_filename(profile_photo.filename)
            profile_photo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            profile_photo.save(profile_photo_path)
            relative_photo_path = os.path.join('uploads', filename)
            updated_data['profile_picture'] = relative_photo_path
        else:
            updated_data['profile_picture'] = data['profile_picture']

        # Update user information in the database
        connection = psycopg2.connect(connection_string)
        cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
        update_query = """
            UPDATE Credentials
            SET fname = %(fname)s, lname = %(lname)s, email = %(email)s,
                phone = %(phone)s, is_admin = %(is_admin)s, 
                facebook = %(facebook)s, twitter = %(twitter)s, 
                instagram = %(instagram)s, linkedin = %(linkedin)s,
                profile_picture = %(profile_picture)s
            WHERE id = %(id)s;
        """

        updated_data['id'] = data['id']

        cursor.execute(update_query, updated_data)
        connection.commit()
        cursor.close()
        connection.close()

        flash('Your profile has been updated successfully! Please login again', category='success')
        return redirect(url_for('login_page'))  # Redirect to login to refresh

    return render_template('edit_profile.html', data=data, form=form)


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
        connection.close()

        flash('Registration successful. Please log in.', category='success')
        return redirect('/patient-login_page')

    return render_template('registration.html', form=form)


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
            cursor.close()  # Close the cursor once
            return redirect('/patient-profile')
        else:
            flash('Incorrect Email or password. Please try again.', category='danger')

    return render_template('patient-login.html', form=LoginForm())


@app.route('/patient-profile')
def patient_profile_page():
    data = session.get('user_data')

    cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
    # Fetch appointments for the current user's ID
    cursor.execute("""
        SELECT appointments.*, radiologist.d_name
        FROM appointments
        JOIN radiologist ON appointments.D_ID = radiologist.d_id
        WHERE P_ID = %s
    """, (data['id'],))
    appointments = cursor.fetchall()
    cursor.close()

    ############################################
    scans_folder = "patient" + str(data['id'])  # make a folder for each patient
    scans_path = os.path.join(app.config['UPLOAD_FOLDER'], scans_folder)
    if os.path.exists(scans_path):
        scan_Files = os.listdir(scans_path)  ## must be absolute path
    else:
        scan_Files = []
    ############################################

    if data is None:
        return redirect('/patient-login')
    return render_template('patient-profile.html', data=data, scan_Files=scan_Files, appointments=appointments)


@app.route('/upload_scan', methods=['GET', 'POST'])
def patient_upload_scan():
    data = session.get('user_data')
    scans_folder = "patient" + str(data['id'])  # make a folder for each patient
    scans_path = os.path.join(app.config['UPLOAD_FOLDER'], scans_folder)
    if data is None:
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
            flash('No scan file selected!', category='danger')

    scan_files = []  # this list stores paths to the scan files
    if os.path.exists(scans_path):
        scan_files = os.listdir(scans_path)
    relative_scan_folder = os.path.join('uploads', scans_folder)
    cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute(
        "UPDATE patient SET scans = %s WHERE id = %s",
        (relative_scan_folder, data['id'])
    )  # insert to the specific patient
    connection.commit()
    cursor.close()

    return render_template('upload_scan.html', data=data, scan_files=scan_files)


@app.route('/patient-edit_profile', methods=['GET', 'POST'])
def patient_edit_profile():
    form = EditProfileForm()
    data = session.get('user_data')

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
            updated_data['profile_picture'] = data['profile_picture']

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
        updated_data['id'] = data['id']

        cursor.execute(update_query, updated_data)
        connection.commit()
        cursor.close()
        connection.close()

        flash('Your profile has been updated successfully! Please login again', category='success')
        return redirect((('/patient-login_page')))  # Redirect to login to refresh

    return render_template('edit_profile.html', data=data, form=form)
