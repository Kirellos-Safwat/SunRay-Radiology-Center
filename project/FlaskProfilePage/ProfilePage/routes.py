import psycopg2.extras
from ProfilePage.forms import RegisterForm, LoginForm , EditProfileForm , PatientRegisterForm
from ProfilePage import app, db, connection , connection_string
from flask import render_template, redirect, url_for, flash, session
from werkzeug.utils import secure_filename
import os
from flask import request

# os.getcwd() might change from devide to device i think , based on your cwd: current working directory
# UPLOAD_FOLDER = os.path.join(os.getcwd(), "project/FlaskProfilePage/ProfilePage/static/uploads")
UPLOAD_FOLDER = os.path.join(os.getcwd(), "project", "FlaskProfilePage", "ProfilePage", "static", "uploads")
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')  # that is the root url of the website
@app.route('/home')
def home_page():
    return render_template('home.html')

@app.route('/edit_data', methods=['POST'])
def edit_data():
    cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
    data = request.get_json()
    if 'delete_id' in data:
        delete_id = data['delete_id']
        print(delete_id)
        update_query = """
            DELETE FROM Credentials 
            WHERE id = %s;
        """
        cursor.execute(update_query, str(delete_id))
    elif 'id' in data:
        update_data = data
        update_query = f"""
            UPDATE Credentials SET 
            {', '.join(
            f"{key} = '{value}'"
            for key, value in update_data.items()
            if key != 'id')}
            WHERE id = {update_data['id']};
        """
        cursor.execute(update_query, update_data)
    cursor.close()    
    connection.commit()
    return redirect(url_for('users_page'))

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
                (fname, lname, email, phone, password, relative_photo_path,is_admin)
                

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
    if os.name == 'nt' and data['profile_picture'] is not None:
        data['profile_picture'] = data['profile_picture'].replace("\\", "/")
    return render_template('profile.html', data=data)


@app.route('/users')
def users_page():
    data = session.get('user_data')
    if data is None or data['is_admin'] == False:
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
    try:
        session.pop('update')
    except:
        pass
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
    scans_folder = "patient" + str(data['id']) # make a folder for each patient
    scans_path = os.path.join(app.config['UPLOAD_FOLDER'], scans_folder)
    if  os.path.exists(scans_path):
        scan_Files = os.listdir(scans_path) ## must be absolute path
    else:
        scan_Files = []
    ############################################
    
    if data is None:
        return redirect('/patient-login')
    return render_template('patient-profile.html', data=data , scan_Files = scan_Files, appointments=appointments)

@app.route('/upload_scan', methods=['GET', 'POST'])
def patient_upload_scan():
    data = session.get('user_data')
    scans_folder = "patient" + str(data['id']) # make a folder for each patient
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
    
    scan_files = [] # this list stores paths to the scan files
    if os.path.exists(scans_path):
        scan_files = os.listdir(scans_path)
    relative_scan_folder = os.path.join('uploads', scans_folder)
    cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute(
         "UPDATE patient SET scans = %s WHERE id = %s",
            (relative_scan_folder, data['id'])
    )# insert to the specific patient
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
        return redirect((('/patient-login_page') )) # Redirect to login to refresh

    return render_template('edit_profile.html', data=data, form=form)
