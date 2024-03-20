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
app.config['DEFAULT_PROFILE_IMAGE'] = 'images/default_profile.png'

mysql = MySQL(app)

# Registration Form
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

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE email = %s', (email,))
        account = cursor.fetchone()

        if account and check_password_hash(account['password'], password):
            session['loggedin'] = True
            session['id'] = account['id']
            session['email'] = account['email']
            flash('Logged in successfully!', 'success')
            return redirect(url_for('profile'))  # Assume a profile page or dashboard
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('email', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))




#****************************** User Profile Managements********************************    

@app.route('/profile')
def profile():
    if 'loggedin' not in session:
        return redirect(url_for('login'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM accounts WHERE id = %s', (session['id'],))
    account = cursor.fetchone()

    profile_image = account['profile_image'] if account['profile_image'] else app.config['DEFAULT_PROFILE_IMAGE']
    profile_image_path = url_for('uploaded_file', filename=profile_image)

    return render_template('profile.html', account=account, profile_image=profile_image_path)


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


# Run the app
if __name__ == '__main__':
    app.run(debug=True)
