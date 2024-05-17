import psycopg2.extras
from ProfilePage.forms import RegisterForm, LoginForm , EditProfileForm
from ProfilePage import app, db, connection , connection_string
from flask import render_template, redirect, url_for, flash, session
from werkzeug.utils import secure_filename
import os
from flask import request

@app.route('/')  # that is the root url of the website
@app.route('/home')
def home_page():
    return render_template('home.html')


# os.getcwd() might change from devide to device i think , based on your cwd: current working directory

# UPLOAD_FOLDER = os.path.join(os.getcwd(), "project/FlaskProfilePage/ProfilePage/static/uploads")
UPLOAD_FOLDER = os.path.join(os.getcwd(), "project", "FlaskProfilePage", "ProfilePage", "static", "uploads")
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


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
