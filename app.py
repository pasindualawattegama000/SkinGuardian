from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, session, send_from_directory, jsonify
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
import json
import uuid
from datetime import datetime

from tensorflow import keras
from tensorflow.keras.preprocessing import image
from tensorflow.keras.applications.imagenet_utils import preprocess_input
import numpy as np



app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = 'your-very-very-secret-key'
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'geeklogin'
app.config['UPLOAD_FOLDER'] = 'static/profile_images'
app.config['DEFAULT_PROFILE_IMAGE'] = 'default_profile.png'
app.config['SKIN_UPLOADS'] = 'static/uploads'
app.config['TEMPORARY_FOLDER'] = 'static/temp_Uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}



# Load the models
auto_scan_model = keras.models.load_model('models/ModelFDC.keras')
cancer_scan_model = keras.models.load_model('models/ModelFSC.keras')
non_cancerous_scan_model = keras.models.load_model('models/ModelFSD.keras')



mysql = MySQL(app)




@app.route('/home', endpoint='home')
def home():
    return render_template('home.html')


# -------------------------Doctor registration form ----------------------------
#                        ADMIN METHODS

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
        contact = form.contact.data  # Get the data from the form

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(
            'INSERT INTO doctors (firstname, lastname, email, password, specialty, contact) VALUES (%s, %s, %s, %s, %s, %s)',
            (firstname, lastname, email, password, specialty, contact)
        ) 
        mysql.connection.commit()
        cursor.close()   

        flash('The new doctor has been successfully registered.', 'success')
        return redirect(url_for('doctorRegister'))  

    return render_template('doctorRegister.html', form=form)



@app.route('/remove_doctors', methods=['GET'])
def remove_doctors():
    if 'loggedin' not in session or session['user_type'] != 'admin':
        return render_template('login.html')
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT id, firstname, lastname, email, specialty, contact FROM doctors')
        doctors = cursor.fetchall()
        return render_template('remove_doctors.html', doctors=doctors)
    except Exception as e:
        flash(f"An error occurred: {e}", "error")
        return redirect(url_for('home'))
    finally:
        cursor.close()


@app.route('/delete_doctor/<int:doctor_id>', methods=['POST'])
def delete_doctor(doctor_id):
    if 'loggedin' not in session or session['user_type'] != 'admin':
        return jsonify({'error': 'Unauthorized access'}), 403

    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('DELETE FROM doctors WHERE id = %s', (doctor_id,))
        mysql.connection.commit()
        cursor.close()

        return jsonify({'success': True, 'message': 'Doctor removed successfully'})
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({'error': 'Failed to remove the doctor'}), 500




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
            if account and check_password_hash(account['password'], password):
                firstname = account['email']
                session['firstname'] = firstname
                session['loggedin'] = True
                session['id'] = account['id']
                session['user_type'] = user_type
                flash('Logged in successfully!', 'success')
                return redirect(url_for('noLoginHome')) 
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


@app.route('/delete_profile', methods=['POST'])
def delete_profile():
    if 'loggedin' not in session:
        return jsonify({'error': 'User not logged in'}), 403

    user_id = session['id']
    user_type = session['user_type']

    print(user_id)

    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        # If the user is a doctor, handle their patient requests and unlink patients
        if user_type == 'doctor':
            cursor.execute('DELETE FROM doctor_requests WHERE doctor_id = %s', (user_id,))
            # cursor.execute('UPDATE accounts SET doctor_id = NULL WHERE doctor_id = %s', (user_id,))
            cursor.execute('DELETE FROM doctors WHERE id = %s', (user_id,))

        # If the user is a patient, remove any pending doctor requests
        elif user_type == 'patient':
            cursor.execute('DELETE FROM doctor_requests WHERE patient_id = %s', (user_id,))
            cursor.execute('DELETE FROM accounts WHERE id = %s', (user_id,))        

        mysql.connection.commit()
        cursor.close()
        session.clear()
        return redirect(url_for('login'), code=302)

    except Exception as e:
        mysql.connection.rollback()
        print(f"An error occurred: {e}")
        flash('Error deleting profile. Please try again.', 'error')
        return redirect(url_for('profile'))



@app.route('/cancel_doctor_request', methods=['POST'])
def cancel_doctor_request():
    if 'loggedin' not in session:
        return jsonify({'error': 'User not logged in'}), 401

    user_id = session['id']
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('DELETE FROM doctor_requests WHERE patient_id = %s', (user_id,))
        mysql.connection.commit()
        cursor.close()
        return jsonify({'success': True, 'message': 'Doctor request cancelled successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500





@app.route('/profile')
def profile():
    if 'loggedin' not in session:
        return redirect(url_for('login'))

    user_type = session.get('user_type')
    user_id = session.get('id')
    has_requested_doctor = False

    if user_type == 'doctor':
        table_name = 'doctors'
    else:
        table_name = 'accounts'  # other users are patients
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM doctor_requests WHERE patient_id = %s', (user_id,))
        has_requested_doctor = cursor.fetchone() is not None
        cursor.close()

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute(f'SELECT * FROM {table_name} WHERE id = %s', (user_id,))
    account = cursor.fetchone()

    if not account:
        flash('User not found.', 'danger')
        return redirect(url_for('home'))

    # Handle displaying default profile image if none exists
    profile_image_path = url_for('static', filename='default_profile.png')  # Default image
    if account.get('profile_image'):
        profile_image_path = url_for('uploaded_file', filename=account['profile_image'])

    return render_template('profile.html', account=account, profile_image=profile_image_path, user_type=user_type, has_requested_doctor=has_requested_doctor)




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



@app.route('/skinuploads/<filename>')
def skin_uploaded_file(filename):
    return send_from_directory(app.config['SKIN_UPLOADS'], filename)



@app.route('/my_uploads')
def my_uploads():
    if 'loggedin' not in session:
        return redirect(url_for('login'))

    user_id = session['id']
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor) 
    
    cursor.execute('SELECT * FROM predictions WHERE user_id = %s ORDER BY uploaded_at ASC LIMIT 1', (user_id,))
    first_prediction = cursor.fetchone()

    cursor.execute('SELECT * FROM predictions WHERE user_id = %s ORDER BY uploaded_at DESC', (user_id,))
    predictions = cursor.fetchall()
    

    if first_prediction:
        first_prediction['image_path'] = first_prediction['image_path'].replace('\\', '/')
    else:
        first_prediction = {'image_path': ''} 

    for prediction in predictions:
        prediction['image_path'] = prediction['image_path'].replace('\\', '/')
    
    cursor.close()

    
    print(predictions) 

    return render_template('my_uploads.html', predictions=predictions, first_prediction=first_prediction if first_prediction else None)




@app.route('/delete_prediction/<int:prediction_id>', methods=['POST'])
def delete_prediction(prediction_id):
    if 'loggedin' not in session:
        return jsonify({'error': 'User not logged in'}), 401

    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        # Retrieve the image path before deletion
        cursor.execute('SELECT image_path FROM predictions WHERE id = %s', (prediction_id,))
        prediction = cursor.fetchone()
        
        if prediction and prediction['image_path']:
            # Delete the prediction from the database
            cursor.execute('DELETE FROM predictions WHERE id = %s', (prediction_id,))
            mysql.connection.commit()

            # Remove the file from the filesystem
            try:
                os.remove(os.path.join(app.config['SKIN_UPLOADS'], prediction['image_path']))
            except OSError as e:
                print(f"Error deleting file: {e}")

        cursor.close()
        return jsonify({'success': True, 'message': 'Prediction deleted successfully'})
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({'error': 'Unable to delete the prediction'}), 500



@app.route('/delete_all_predictions', methods=['POST'])
def delete_all_predictions():
    if 'loggedin' not in session:
        return jsonify({'error': 'User not logged in'}), 401
    
    user_id = session.get('id')
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        # Retrieve all image paths before deletion
        cursor.execute('SELECT image_path FROM predictions WHERE user_id = %s', (user_id,))
        predictions = cursor.fetchall()

        for prediction in predictions:
            if prediction['image_path']:
                try:
                    os.remove(os.path.join(app.config['SKIN_UPLOADS'], prediction['image_path']))
                except OSError as e:
                    print(f"Error deleting file: {e}")

        # After deleting the files, clear the records from the database
        cursor.execute('DELETE FROM predictions WHERE user_id = %s', (user_id,))
        mysql.connection.commit()

        cursor.close()
        return jsonify({'success': True, 'message': 'All predictions deleted'})
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({'error': 'Unable to delete predictions'}), 500




# ----------------------------------------------------------------------------------------------
#                        SCAN IMAGES FUNCTIONALITY

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def prepare_image(file_path, target_size=(200, 200)):
    img = image.load_img(file_path, target_size=target_size)
    img_array = image.img_to_array(img)
    img_array_expanded_dims = np.expand_dims(img_array, axis=0)
    return preprocess_input(img_array_expanded_dims)


def interpret_prediction(model_name, prediction):
    if model_name == 'cancer_scan_model':
        class_labels = ['Actinic Keratoese', 'Basal Cell Carcinoma', 'Melanocytic Nevi', 'Melanoma']
        predicted_class = class_labels[np.argmax(prediction)]

    elif model_name == 'non_cancerous_scan_model':
        class_labels = ['Acne', 'Bacterial Infections', 'bkl', 'df', 'Eczema', 'Herpes', 'Lentigo', 'Normal Skin', 'Porphyrias', 'Psoriasis', 'Vasculitis Photos', 'Vitiligo', 'Warts']
        predicted_class = class_labels[np.argmax(prediction)]
    else:
        predicted_class = 'Unknown Model'
    
    return predicted_class


@app.route('/scan', methods=['POST'])
def scan_image():
    # print(request.form)
    # print(request.form.get('savePrediction'))

    if 'loggedin' not in session:
        return render_template('noLoginHome.html')


    if 'skinImage' not in request.files:
        flash('No file part')
        return redirect(request.url)
    
    file = request.files['skinImage']
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    
    if file and allowed_file(file.filename):
        user_id = session['id']  # Retrieve user ID from session
        original_filename = secure_filename(file.filename)
        file_ext = original_filename.rsplit('.', 1)[1].lower()  # Get file extension
        
        # Generate a unique filename using the user's ID and a UUID
        unique_filename = f"user_{user_id}_{uuid.uuid4().hex}.{file_ext}"
        
        filepath = os.path.join(app.config['SKIN_UPLOADS'], unique_filename)
        file.save(filepath)
        
        scan_type = request.form.get('scanType')
 
        #Preprocessing the input image
        preprocessed_Img = prepare_image(filepath)

        disease_type = ''
        disease_class = ''

        if scan_type == 'autoScan':
            model = auto_scan_model
            ML_prediction = model.predict(preprocessed_Img)

            if ML_prediction == [[0.]]:
                disease_type = "Non cancerous"

                model = non_cancerous_scan_model
                model_name = 'non_cancerous_scan_model'
                ML_prediction = model.predict(preprocessed_Img)
                disease_class = interpret_prediction(model_name, ML_prediction)
                print('non cancerous')
            else:
                disease_type = "Cancerous"

                model = cancer_scan_model
                model_name = 'cancer_scan_model'
                ML_prediction = model.predict(preprocessed_Img)
                disease_class = interpret_prediction(model_name, ML_prediction)
                print('cancerous')


        elif scan_type == 'cancerScan':
            disease_type = "Cancerous"

            model = cancer_scan_model
            model_name = 'cancer_scan_model'
            ML_prediction = model.predict(preprocessed_Img)

            disease_class = interpret_prediction(model_name, ML_prediction)


        elif scan_type == 'nonCancerousScan':
            disease_type = "Non cancerous"

            model = non_cancerous_scan_model
            model_name = 'non_cancerous_scan_model'
            ML_prediction = model.predict(preprocessed_Img)

            disease_class = interpret_prediction(model_name, ML_prediction)



        else:
            return jsonify({'error': 'Invalid scan type specified'}), 400


        prediction_details = f"Disease Type: {disease_type}\nDisease Class: {disease_class}"

# ----------------------------------------------------------------------

        if 'savePrediction' in request.form and request.form['savePrediction'] == 'true':
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute(
                'INSERT INTO predictions (user_id, image_path, prediction_details) VALUES (%s, %s, %s)',
                (user_id, unique_filename, prediction_details)
            )
            mysql.connection.commit()
            cursor.close()
            
            return jsonify({'success': True, 'message': 'Your prediction has been saved.', 'prediction': prediction_details})
        else:
            os.remove(filepath)  # Delete the file
            return jsonify({'success': True, 'message': 'Your prediction was not saved.', 'prediction': prediction_details})
        

    else:
        flash('Invalid file type')
        return redirect(request.url)




# ----------------------------------------------------------------------------------------------------


@app.route('/doctors')
def doctors_list():
    if 'loggedin' not in session:
        return redirect(url_for('login'))  # Redirect to login page if not logged in

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM doctors ORDER BY lastname, firstname')
    doctors = cursor.fetchall()
    cursor.close()
    return render_template('doctors_list.html', doctors=doctors)


@app.route('/my_doctor')
def my_doctor():
    if 'loggedin' not in session or session['user_type'] != 'patient':
        return redirect(url_for('login'))  # Only logged-in patients can view their doctor

    user_id = session.get('id')
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT doctor_id FROM accounts WHERE id = %s', (user_id,))
    account = cursor.fetchone()

    if account and account['doctor_id']:
        cursor.execute('SELECT * FROM doctors WHERE id = %s', (account['doctor_id'],))
        doctor = cursor.fetchone()
        cursor.close()

        profile_image = doctor.get('profile_image', app.config['DEFAULT_PROFILE_IMAGE'])
        profile_image_path = url_for('uploaded_file', filename=profile_image)

        return render_template('my_doctor.html', doctor=doctor, profile_image=profile_image_path)
    else:
        cursor.close()
        flash('No doctor assigned to your account.', 'warning')
        return render_template('my_doctor.html', doctor=None)




@app.route('/remove_doctor/<int:doctor_id>', methods=['POST'])
def remove_doctor(doctor_id):
    if 'loggedin' not in session or session['user_type'] != 'patient':
        return jsonify({'error': 'Not authorized'}), 403

    user_id = session.get('id')
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('UPDATE accounts SET doctor_id = NULL WHERE id = %s', (user_id,))
        mysql.connection.commit()
        cursor.close()
        return jsonify({'success': True, 'message': 'Doctor removed successfully'})
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({'error': 'Unable to remove doctor'}), 500



@app.route('/request_doctor/<int:doctor_id>', methods=['POST'])
def request_doctor(doctor_id):
    if 'loggedin' not in session or session['user_type'] != 'patient':
        return jsonify({'error': 'Unauthorized'}), 401

    patient_id = session['id']

    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        # Check if a request already exists or patient already has a doctor
        cursor.execute('SELECT * FROM doctor_requests WHERE patient_id = %s', (patient_id,))
        existing_request = cursor.fetchone()
        if existing_request:
            return jsonify({'error': 'You have already sent a request.'}), 400

        cursor.execute('SELECT doctor_id FROM accounts WHERE id = %s', (patient_id,))
        account = cursor.fetchone()
        if account['doctor_id']:
            return jsonify({'error': 'You already have a doctor.'}), 400

        # Insert new request
        cursor.execute(
            'INSERT INTO doctor_requests (patient_id, doctor_id) VALUES (%s, %s)',
            (patient_id, doctor_id)
        )
        mysql.connection.commit()
        cursor.close()
        return jsonify({'success': True, 'message': 'Doctor request sent successfully'})
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({'error': 'Unable to send doctor request'}), 500


#----------------------------------------------------------------------------------------------
# Doctor Methods Implimentation

from flask import flash, redirect, url_for

@app.route('/patient_requests', methods=['GET'])
def patient_requests():
    if 'loggedin' not in session or session['user_type'] != 'doctor':
        # Unauthorized access, redirect to login page
        flash('Please log in to view patient requests.', 'warning')
        return redirect(url_for('login'))

    doctor_id = session['id']
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        cursor.execute('''
            SELECT r.id AS request_id, a.id AS patient_id, CONCAT(a.firstname, ' ', a.lastname) AS patient_name, a.contact, a.email 
            FROM doctor_requests r
            JOIN accounts a ON r.patient_id = a.id
            WHERE r.doctor_id = %s
        ''', (doctor_id,))
        requests = cursor.fetchall()
        return render_template('patient_requests.html', requests=requests)
    except Exception as e:
        print(f"An error occurred: {e}")
        flash('Failed to retrieve patient requests.', 'error')
        return render_template('error_page.html')  
    finally:
        cursor.close()




@app.route('/accept_patient_request/<int:request_id>', methods=['POST'])
def accept_patient_request(request_id):
    if 'loggedin' not in session or session['user_type'] != 'doctor':
        return jsonify({'error': 'Unauthorized access'}), 403

    doctor_id = session['id']
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        # Retrieve the patient_id from doctor_requests table
        cursor.execute('SELECT patient_id FROM doctor_requests WHERE id = %s', (request_id,))
        patient_request = cursor.fetchone()

        if patient_request:
            patient_id = patient_request['patient_id']
            # Update the accounts table to link patient with doctor
            cursor.execute('UPDATE accounts SET doctor_id = %s WHERE id = %s', (doctor_id, patient_id))
            # Delete the request from doctor_requests table
            cursor.execute('DELETE FROM doctor_requests WHERE id = %s', (request_id,))
            mysql.connection.commit()
            return jsonify({'success': True, 'message': 'Patient request accepted'})
        else:
            return jsonify({'error': 'Request not found'}), 404
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({'error': 'Failed to accept patient request'}), 500
    finally:
        cursor.close()







@app.route('/my_patients', methods=['GET'])
def my_patients():
    if 'loggedin' not in session or session['user_type'] != 'doctor':
        flash("Unauthorized access. Please login as a doctor.", "danger")
        return redirect(url_for('login'))

    doctor_id = session['id']
   
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT id, firstname, lastname, email FROM accounts WHERE doctor_id = %s', (doctor_id,))
        patients = cursor.fetchall()
        print(patients)
        return render_template('my_patients.html', patients=patients)
    except Exception as e:
        print("error")
        flash(f"An error occurred: {e}", "error")
        return redirect(url_for('home'))
    finally:
        cursor.close()


@app.route('/patient_uploads/<int:patient_id>', methods=['GET'])
def patient_uploads(patient_id):
    # Ensure the doctor is logged in and is linked to the patient
    if 'loggedin' not in session or session['user_type'] != 'doctor':
        flash("Unauthorized access. Please login as a doctor.", "danger")
        return redirect(url_for('login'))

    doctor_id = session['id']
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE id = %s AND doctor_id = %s', (patient_id, doctor_id))
        patient = cursor.fetchone()
        if not patient:
            flash("You do not have access to this patient's uploads.", "danger")
            return redirect(url_for('my_patients'))

        # Fetch patient's uploads if the doctor is linked
        cursor.execute('SELECT * FROM predictions WHERE user_id = %s', (patient_id,))
        predictions = cursor.fetchall()
        return render_template('patient_uploads.html', predictions=predictions, patient=patient)
    except Exception as e:
        flash(f"An error occurred: {e}", "error")
        return redirect(url_for('my_patients'))
    finally:
        cursor.close()


#-----------------------------------------------------------------------------
#                    NON ACCOUNT USERS

@app.route('/')
@app.route('/noLoginHome', endpoint='noLoginHome')
def noLoginHome():
    return render_template('noLoginHome.html')

@app.route('/scan_no_account', methods=['POST'])
def scan_no_account():
    if 'skinImage' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['skinImage']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file and allowed_file(file.filename):
        file_ext = file.filename.rsplit('.', 1)[1].lower()
        unique_filename = f"temp_{uuid.uuid4().hex}.{file_ext}"
        temp_filepath = os.path.join(app.config['TEMPORARY_FOLDER'], unique_filename)
        file.save(temp_filepath)

        scan_type = request.form.get('scanType')
        disease_type = ''
        disease_class = ''
        preprocessed_Img = prepare_image(temp_filepath)

        if scan_type == 'autoScan':
            model = auto_scan_model
            ML_prediction = model.predict(preprocessed_Img)

            if ML_prediction == [[0.]]:
                disease_type = "Non cancerous"

                model = non_cancerous_scan_model
                model_name = 'non_cancerous_scan_model'
                ML_prediction = model.predict(preprocessed_Img)
                disease_class = interpret_prediction(model_name, ML_prediction)
                print('non cancerous')
            else:
                disease_type = "Cancerous"

                model = cancer_scan_model
                model_name = 'cancer_scan_model'
                ML_prediction = model.predict(preprocessed_Img)
                disease_class = interpret_prediction(model_name, ML_prediction)
                print('cancerous')


        elif scan_type == 'cancerScan':
            disease_type = "Cancerous"

            model = cancer_scan_model
            model_name = 'cancer_scan_model'
            ML_prediction = model.predict(preprocessed_Img)

            disease_class = interpret_prediction(model_name, ML_prediction)


        elif scan_type == 'nonCancerousScan':
            disease_type = "Non cancerous"

            model = non_cancerous_scan_model
            model_name = 'non_cancerous_scan_model'
            ML_prediction = model.predict(preprocessed_Img)

            disease_class = interpret_prediction(model_name, ML_prediction)



        else:
            return jsonify({'error': 'Invalid scan type specified'}), 400

        prediction_details = f"Disease Type: {disease_type}\nDisease Class: {disease_class}"
        # Delete the temporary file after prediction
        os.remove(temp_filepath)

        return jsonify({'success': True, 'message': 'Prediction made successfully.', 'prediction': prediction_details})
    else:
        return jsonify({"error": "Invalid file type"}), 400


# Run the app
if __name__ == '__main__':
    app.run(debug=True)
