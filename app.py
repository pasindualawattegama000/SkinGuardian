from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, session, send_from_directory
)
from flask_wtf import FlaskForm
from wtforms import (
    StringField, PasswordField, SubmitField,
    SelectField, DateField
)
from wtforms.validators import InputRequired, Email, Length, ValidationError
from flask_mysqldb import MySQL
import MySQLdb.cursors
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os


app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = 'your-very-very-secret-key'
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'geeklogin'
app.config['UPLOAD_FOLDER'] = 'static/profile_images'
app.config['DEFAULT_PROFILE_IMAGE'] = 'default_profile.png'

mysql = MySQL(app)



@app.route('/')
@app.route('/home', endpoint='home')
def home():
    return render_template('home.html')


# -------------------------Doctor registration form ----------------------------

# Doctor Registration Form
class DoctorRegistrationForm(FlaskForm):
    firstname = StringField('First Name', validators=[InputRequired(), Length(min=1, max=50)])
    lastname = StringField('Last Name', validators=[InputRequired(), Length(min=1, max=50)])
    email = StringField('Email', validators=[InputRequired(), Email(message='Invalid email'), Length(max=100)])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=8)])
    specialty = StringField('Specialty', validators=[InputRequired()])
    contact = StringField('Contact Number', validators=[InputRequired(), Length(min=10, max=15)])
    submit = SubmitField('Register Doctor')

    # Custom validator to check if email already exists in the doctors table
    def validate_email(self, email):
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM doctors WHERE email = %s', (email.data,))
        doctor = cursor.fetchone()
        if doctor:
            raise ValidationError('An email address already exists.')


@app.route('/doctorRegister', methods=['GET', 'POST'])
def doctorRegister():
    if not session.get('loggedin') or session.get('user_type') != 'admin':
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('login'))

    form = DoctorRegistrationForm(request.form)
 
    if form.validate_on_submit():
        firstname = form.firstname.data
        lastname = form.lastname.data
        email = form.email.data
        password = generate_password_hash(form.password.data)
        specialty = form.specialty.data
        contact = form.contact.data  # Get the contact data from the form

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(
            'INSERT INTO doctors (firstname, lastname, email, password, specialty, contact) VALUES (%s, %s, %s, %s, %s, %s)',
            (firstname, lastname, email, password, specialty, contact)
        ) 
        mysql.connection.commit()
        cursor.close()   

        flash('The new doctor has been successfully registered.', 'success')
        return redirect(url_for('doctorRegister'))  # Redirect to an admin dashboard or other appropriate page.

    return render_template('doctorRegister.html', form=form)





# -------------------------Patient registration form ----------------------------
class RegistrationForm(FlaskForm):
    firstname = StringField('First Name', validators=[InputRequired(), Length(min=1, max=50)])
    lastname = StringField('Last Name', validators=[InputRequired(), Length(min=1, max=50)])
    dob = DateField('Date of Birth', format='%Y-%m-%d', validators=[InputRequired()])
    gender = SelectField('Gender', choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')], validators=[InputRequired()])
    contact = StringField('Contact Number', validators=[InputRequired(), Length(min=10, max=15)])
    email = StringField('Email', validators=[InputRequired(), Email(message='Invalid email'), Length(max=100)])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=8, max=255)])
    submit = SubmitField('Register')

    # Custom validator for email
    def validate_email(self, email):
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE email = %s', (email.data,))
        account = cursor.fetchone()
        if account:
            raise ValidationError('An account with this email already exists.')


# Login Form
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[InputRequired(), Email()])
    password = PasswordField('Password', validators=[InputRequired()])
    user_type = SelectField('Login As', choices=[('patient', 'Patient'), ('doctor', 'Doctor'), ('admin', 'Admin')])
    submit = SubmitField('Login')

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm(request.form)
    if form.validate_on_submit():
        firstname = form.firstname.data
        lastname = form.lastname.data
        dob = form.dob.data.strftime('%Y-%m-%d')  # Formatting the date to a string for MySQL
        gender = form.gender.data
        contact = form.contact.data
        email = form.email.data
        password = generate_password_hash(form.password.data)  # Hashing the password

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('INSERT INTO accounts (firstname, lastname, dob, gender, contact, email, password) VALUES (%s, %s, %s, %s, %s, %s, %s)', (firstname, lastname, dob, gender, contact, email, password))
        mysql.connection.commit()
        cursor.close()

        flash('You have successfully registered! You can now login.', 'success') #alerting the user that the registration was successfull.
        return redirect(url_for('login'))
    return render_template('register.html', form=form)




@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm(request.form)
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        user_type = form.user_type.data

        if user_type == 'doctor':
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM doctors WHERE email =%s',(email,))

        elif user_type == 'admin':
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM admins WHERE email =%s',(email,))

        else:
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM accounts WHERE email =%s',(email,))


        account = cursor.fetchone()


        if user_type == "doctor":
            if account and check_password_hash(account['password'], password):
                firstname= account['firstname']
                lastname = account['lastname']
                fullname = firstname +" " +lastname
                session['fullname'] = fullname
                session['email'] = account['email']
                
                session['loggedin'] = True
                session['id'] = account['id']
                session['user_type'] = user_type
                flash('Logged in successfully!', 'success')
                return redirect(url_for('profile'))  # Loading profile page when login successful.
            else:
                flash( 'Login Unsuccessful. Please check email and password', 'danger')
                #flash(user_type, 'danger')



        elif user_type == "admin":
            if account and account['password'] == password:
                firstname = account['email']
                session['firstname'] = firstname
                session['loggedin'] = True
                session['id'] = account['id']
                session['user_type'] = user_type
                flash('Logged in successfully!', 'success')
                return redirect(url_for('home')) 
            else:
                flash('Admin Login Unsuccessful. Please check email and password', 'danger')
        
        else:
            if account and check_password_hash(account['password'], password):
                firstname= account['firstname']
                lastname = account['lastname']
                fullname = firstname +" " +lastname
                session['fullname'] = fullname
                session['email'] = account['email']
                
                session['loggedin'] = True
                session['id'] = account['id']
                session['user_type'] = user_type
                flash('Logged in successfully!', 'success')
                return redirect(url_for('profile'))  # Loading profile page when login successful.
            else:
                flash('Login Unsuccessful. Please check email and password', 'danger')
                #flash(user_type, 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('email', None)
    session.pop('fullname',None)
    session.pop('user_type',None)
    try:
        session['_flashes'] = []  
    except KeyError:
        pass  

    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))




#****************************** User Profile Managements********************************    

# @app.route('/profile')
# def profile():
#     if session['user_type'] == 'admin':
#         return redirect(url_for('home'))

#     if 'loggedin' not in session:
#         return redirect(url_for('login'))

#     cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
#     cursor.execute('SELECT * FROM accounts WHERE id = %s', (session['id'],))
#     account = cursor.fetchone()

#     profile_image = account['profile_image'] if account['profile_image'] else app.config['DEFAULT_PROFILE_IMAGE']
#     profile_image_path = url_for('uploaded_file', filename=profile_image)

#     return render_template('profile.html', account=account, profile_image=profile_image_path)



@app.route('/profile')
def profile():
    if 'loggedin' not in session:
        return redirect(url_for('login'))

    user_type = session.get('user_type')
    user_id = session.get('id')

    if user_type == 'doctor':
        table_name = 'doctors'
    else:
        table_name = 'accounts'  # Assuming all other users are patients for simplicity

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute(f'SELECT * FROM {table_name} WHERE id = %s', (user_id,))
    account = cursor.fetchone()

    if not account:
        flash('User not found.', 'danger')
        return redirect(url_for('home'))

    # Handle displaying default profile image if none exists
    profile_image = account.get('profile_image', app.config['DEFAULT_PROFILE_IMAGE'])
    profile_image_path = url_for('uploaded_file', filename=profile_image)

    return render_template('profile.html', account=account, profile_image=profile_image_path, user_type=user_type)




@app.route('/update_profile', methods=['POST'])
def update_profile():
    if 'loggedin' not in session:
        return redirect(url_for('login'))

    firstname = request.form['firstname']
    lastname = request.form['lastname']
    contact = request.form['contact']
    new_password = request.form['password'].strip()

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    if new_password:
        hashed_password = generate_password_hash(new_password)
        cursor.execute('UPDATE accounts SET firstname = %s, lastname = %s, contact = %s, password = %s WHERE id = %s', (firstname, lastname, contact, hashed_password, session['id']))
    else:
        cursor.execute('UPDATE accounts SET firstname = %s, lastname = %s, contact = %s WHERE id = %s', (firstname, lastname, contact, session['id']))

    mysql.connection.commit()
    flash('Your profile has been updated successfully!', 'success')

    return redirect(url_for('profile'))




@app.route('/upload', methods=['POST'])
def upload():
    if 'loggedin' not in session:
        return redirect(url_for('login'))

    if 'profile_image' in request.files:
        file = request.files['profile_image']
        if file.filename != '':
            filename = secure_filename(file.filename)
            unique_filename = f"user_{session['id']}_{filename}"

            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT profile_image FROM accounts WHERE id = %s', (session['id'],))
            account = cursor.fetchone()
            old_image = account.get('profile_image') if account else None

            if old_image and os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], old_image)):
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], old_image))

            file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(file_path)

            cursor.execute('UPDATE accounts SET profile_image = %s WHERE id = %s', (unique_filename, session['id']))
            mysql.connection.commit()
            flash('Your profile image has been updated!', 'success')

    return redirect(url_for('profile'))


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/myUploads')
def myUploads():
    pass

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
