import psycopg2.extras
from sqlalchemy.testing.plugin.plugin_base import post
from ProfilePage import app, db, connection, connection_string, mail, bcrypt,flow, GOOGLE_CLIENT_ID
from flask_login import current_user
from flask_mail import Message
from ProfilePage.models import appointments, Patient
from ProfilePage.forms import LoginForm, EditProfileForm, AppointmentForm, PatientRegisterForm, ReportForm, \
    RadiologistRegisterForm, ForgetForm, \
    ResetPasswordForm, SearchForm
from flask import render_template, redirect, url_for, flash, session, request
from werkzeug.utils import secure_filename
import os, psycopg2.extras, random
import requests
from google.oauth2 import id_token
from pip._vendor import cachecontrol
import google.auth.transport.requests


@app.route('/')  # that is the root url of the website
@app.route('/home')
def home_page():
    data = session.get('user_data')
    return render_template('home.html', data=data)


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
            return redirect(url_for('patient_profile_page'))
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
        d_id = data['d_id']

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
            return redirect(url_for('radiologist_profile_page'))
    return render_template('report.html', form=form, data=data)


'''
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
                return redirect(url_for('login_admin')) 
            else:
                flash('Invalid email or password. Please try again.', category='danger')

        return render_template('registration.html', form=RegisterForm())
'''


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
            cursor.close()  # Close the cursor once
            return redirect('/users')
        else:
            flash('Incorrect Email or password. Please try again.', category='danger')

    return render_template('login.html', form=LoginForm())


'''
    @app.route('/profile')
    def profile_page():
        data = session.get('user_data')
        if data is None:
            return redirect('/login')
        if os.name == 'nt' and data['profile_picture'] is not None:
            data['profile_picture'] = data['profile_picture'].replace("\\", "/")
        return render_template('profile.html', data=data)
'''


@app.route('/users')
def users_page():
    data = session.get('user_data')
    if data is None or 'admin_id' not in data:
        return redirect('/login')
    cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute('SELECT * FROM patient')
    # patients data
    patients = cursor.fetchall()
    cursor.execute('SELECT * FROM radiologist')
    # doctors data
    doctors = cursor.fetchall()
    cursor.close()
    return render_template('users.html', patients=patients, doctors=doctors)


@app.route('/logout')
def logout():
    session.pop('user_data')
    try:
        session.pop('update')
    except:
        pass
    return redirect('/')


@app.route('/done')
def thanks_page():
    return render_template('thank_you.html')


'''
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
            return redirect(url_for('login_admin'))  # Redirect to login to refresh

        return render_template('edit_profile.html', data=data, form=form)



@app.route('/radiologist-register', methods=['GET', 'POST'])
def radiologist_registration_page():
    form = RadiologistRegisterForm()
    if form.validate_on_submit():
        d_name = form.D_Name.data
        d_email = form.Email.data
        print(d_email)
        d_phone = form.Phone_Number.data
        d_password = form.Password.data

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
            "INSERT INTO radiologist (d_name,d_email, d_phone, d_password, d_profile_picture) VALUES (%s, %s, %s, %s, %s)",
            (d_name, d_email, d_phone, d_password, relative_photo_path)
        )
        connection.commit()
        cursor.close()
        connection.close()

        flash('Registration successful. Please log in.', category='success')
        return redirect('/radiologist-login_page')

    return render_template('radiologist-registration.html', form=form)

'''
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
                data['profile_picture'] = data['profile_picture'].replace("\\", "/")
            cursor.close()  # Close the cursor once
            return redirect('/radiologist-profile')
        else:
            flash('Incorrect Email or password. Please try again.', category='error')

    return render_template('radiologist-login.html', form=LoginForm())  # check render


@app.route('/radiologist-profile')
def radiologist_profile_page():
    data = session.get('user_data')

    cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
    # Fetch appointments for the current user's ID
    cursor.execute("""
            SELECT appointments.*, patient.fname, patient.lname
            FROM appointments
            JOIN patient ON appointments.p_id = patient.id
            WHERE appointments.d_id = %s
        """, (data['d_id'],))
    appointments = cursor.fetchall()
    cursor.close()

    if data is None:
        return redirect('/radiologist-login')
    return render_template('radiologist-profile.html', data=data, appointments=appointments)


@app.route('/radiologist-edit_profile', methods=['GET', 'POST'])
def radiologist_edit_profile():
    form = EditProfileForm()
    data = session.get('user_data')

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
            updated_data['profile_picture'] = data['profile_picture']

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
        updated_data['d_id'] = data['d_id']

        cursor.execute(update_query, updated_data)
        connection.commit()
        cursor.close()
        connection.close()

        flash('Your profile has been updated successfully! Please login again', category='success')
        return redirect('/radiologist-login_page')  # Redirect to log in to refresh

    return render_template('radiologist_edit_profile.html', data=data, form=form)


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
            data = session['user_data']
            if os.name == 'nt' and data['scans'] is not None:
                data['scans'] = data['scans'].replace("\\", "/")
            if os.name == 'nt' and data['profile_picture'] is not None:
                data['profile_picture'] = data['profile_picture'].replace("\\", "/")
            cursor.close()  # Close the cursor once
            return redirect('/patient-profile')
        else:
            flash('Incorrect Email or password. Please try again.', category='error')

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
        scan_Files = os.listdir(scans_path)  # must be absolute path
    else:
        scan_Files = []
    ############################################
    # if os.name == 'nt' and data['scans'] is not None:
    #     data['scans'] = data['scans'].replace("\\", "/")
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
        return redirect('/patient-login_page')  # Redirect to log in to refresh

    return render_template('edit_profile.html', data=data, form=form)


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
    return render_template('contact.html')


@app.route('/search', methods=["POST"])
def search():
    form = SearchForm()
    names = Patient.query
    if form.validate_on_submit():
        # Get data from submitted form
        post.searched = form.searched.data
        # Query the Database
        names = names.filter(Patient.fname.like('%' + post.searched + '%'))
        names = names.order_by(Patient.id).all()
        return render_template("search.html",
                               form=form,
                               searched=post.searched, names=names)


@app.context_processor
def base():
    form = SearchForm()
    return dict(form=form)


'''
    @app.route('/posts')
    def posts():
        # Grab all the posts from the database
        posts = Posts.query.order_by(Posts.date_posted)
        return render_template("posts.html", posts=posts)
'''


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
    return render_template("forgetPassword.html", form=form)


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
    data = session.get('user_data')
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
        updated_data['id'] = data['id']

        cursor.execute(update_query, updated_data)
        connection.commit()
        cursor.close()
        connection.close()

        flash('Your password has been updated successfully! You are now able to log in', category='success')
        return redirect('/patient-login_page')  # Redirect to log in to refresh
    return render_template("ResetPassword.html", form=form)


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
    return redirect("/patient-profile")
