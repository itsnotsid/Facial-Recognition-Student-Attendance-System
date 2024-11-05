from flask import request, redirect, url_for
from flask import Flask, render_template, jsonify, Response
import base64
from pymongo import MongoClient
from flask_pymongo import PyMongo
from flask import send_file
from io import BytesIO, StringIO
from bson import ObjectId
import traceback  # Import the traceback module
from bson.binary import Binary
import cv2
import numpy as np
import face_recognition
import os
from datetime import datetime, timedelta
import dlib
from PIL import Image
import time
import csv


app = Flask(__name__)
camera = cv2.VideoCapture(0)
# MongoDB configuration
app.config['MONGO_URI'] = 'mongodb://localhost:27017/student_data'
mongo = PyMongo(app)

# MongoDB connection
client = MongoClient('mongodb://localhost:27017/')
db = client['student_data']
students_collection = db['students']
users_collection = db['users']
collection = db['students']
images_collection = db['images']
training_images = db['images']

# Initialize an empty list to store student data
students = []
images = []
classNames = []


@app.route('/')
def index():
    return render_template('login.html')


@app.route('/addstudent')
def addstudent():
    return render_template('addstudent.html')


@app.route('/signup')
def signup():
    return render_template('signup.html')


@app.route('/forgotpass')
def forgotpass():
    return render_template('forgotpass.html')


@app.route('/attendance')
def attendance():
    return render_template('attendance.html')


@app.route('/studentdetails')
def studentdetails():
    return render_template('studentdetails.html')


@app.route('/searchstudent')
def searchstudent():
    return render_template('searchstudent.html')


@app.route('/dashboard')
def dashboard():
    camera.release()
    return render_template('dashboard.html')


@app.route('/index')
def login():
    return render_template('index.html')


@app.route('/submit', methods=['POST'])
def submit():
    if request.method == 'POST':
        # Access form data using request.form.get() to avoid KeyError if the key doesn't exist
        fname = request.form.get('fname', '')
        lname = request.form.get('lname', '')
        gender = request.form.get('gender', '')
        dob = request.form.get('dob', '')
        email = request.form.get('email', '')
        phone_number = request.form.get('phone_number', '')
        register = request.form.get('register', '')
        address = request.form.get('address', '')
        state = request.form.get('state', '')
        pincode = request.form.get('pincode', '')
        declaration = request.form.get('check', '')

        # Insert data into MongoDB
        student_data = {
            'fname': fname,
            'lname': lname,
            'gender': gender,
            'dob': dob,
            'email': email,
            'phone_number': phone_number,
            'register': register,
            'address': address,
            'state': state,
            'pincode': pincode,
            'declaration': declaration
        }
        students_collection.insert_one(student_data)
        return jsonify({'message': 'Student registered successfully'}), 200


@app.route('/saveImage', methods=['POST'])
def save_image():
    try:
        data = request.json
        image_data = data['image']
        student_id = data['register']

        # Decode the base64-encoded image data
        image_bytes = base64.b64decode(image_data.split(',')[1])

        # Convert the image bytes to BSON Binary for MongoDB
        image_binary = Binary(image_bytes)

        # Save image data along with student ID
        images_collection.insert_one(
            {'student_id': student_id, 'imageData': image_binary})

        return jsonify({'message': 'Image saved successfully'}), 200
    except Exception as e:
        print('Error saving image:', str(e))
        return jsonify({'error': 'Internal Server Error'}), 500


@app.route('/getImage/<image_id>', methods=['GET'])
def get_image(image_id):
    try:
        image_data = images_collection.find_one({'student_id': image_id})
        if image_data:
            # Return the image data as a file
            return send_file(BytesIO(image_data['imageData']), mimetype='image/jpeg')
        else:
            return jsonify({'error': 'Image not found'}), 404
    except Exception as e:
        print('Error fetching image:', str(e))
        return jsonify({'error': 'Internal Server Error'}), 500


@app.route('/entries', methods=['GET'])
def get_entries():
    try:
        # Fetch all entries from the MongoDB collection
        entries = students_collection.find()

        # Convert entries to a list of dictionaries
        entries_list = []
        for entry in entries:
            entry_dict = {
                'id': str(entry['_id']),  # Convert ObjectId to string
                'fname': entry['fname'],
                'lname': entry['lname'],
                'gender': entry['gender'],
                'dob': entry['dob'],
                'email': entry['email'],
                'phone_number': entry['phone_number'],
                'register': entry['register'],
                'address': entry['address'],
                'state': entry['state'],
                'pincode': entry['pincode'],
                'declaration': entry['declaration']
            }
            entries_list.append(entry_dict)

        # Return entries as JSON response
        return jsonify(entries_list), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/register', methods=['POST'])
def register():
    # Get user data from request body
    data = request.json
    email = data.get('email')
    password = data.get('password')

    # Check if email or password is missing
    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400

    # Check if the email already exists in the database
    if users_collection.find_one({'email': email}):
        return jsonify({'error': 'Email already exists'}), 400

    # Insert new user into the database
    users_collection.insert_one({'email': email, 'password': password})

    # Return a success response
    return jsonify({'message': 'User registered successfully'}), 201


@app.route('/signin', methods=['POST'])
def signin():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    # Check if email and password are provided
    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400

    # Check if user exists in the database
    user = users_collection.find_one({'email': email})

    if user and user['password'] == password:
        # User credentials are correct, return a success response
        return jsonify({'message': 'Login successful'}), 200
    else:
        # Invalid credentials, return an error response
        return jsonify({'error': 'Invalid email or password'}), 401


# Define a dictionary to store user data
users = {}

# Endpoint to list all students


@app.route('/liststudents', methods=['GET'])
def list_students():
    students = collection.find()
    stuData = []
    for document in students:
        document['_id'] = str(document['_id'])
        stuData.append(document)
    print(stuData)
    return jsonify(stuData)


@app.route("/edit", methods=["GET", "POST"])
def edit_student():
    if request.method == "POST":
        # Update student details in the database
        print(request.form['id'])
        students_collection.update_one(
            {"_id": request.form['id']},
            {
                "$set": {
                    "fname": request.form["fname"],
                    "lname": request.form["lname"],
                    "gender": request.form["gender"],
                    "dob": request.form["dob"],
                    "email": request.form["email"],
                    "phone_number": request.form["phone_number"],
                    "address": request.form["address"],
                    "state": request.form["state"],
                    "pincode": request.form["pincode"]
                }
            }
        )
        return redirect(url_for("dashboard"))

    # Retrieve student details from the database
    return render_template("edit_student.html")

# Define your route to handle POST requests for updating student details


@app.route('/update_student', methods=['POST'])
def update_student():
    try:
        # Parse the form data from the request
        student_data = request.form

        # Extract individual fields from the form data
        student_id = student_data.get('id')
        fname = student_data.get('fname')
        lname = student_data.get('lname')
        email = student_data.get('email')
        phone_number = student_data.get('phone_number')
        address = student_data.get('address')
        state = student_data.get('state')
        pincode = student_data.get('pincode')

        print({
            "id": student_id,
            "fname": fname,
            "lname": lname,
            "email": email,
            "phone_number": phone_number,
            "address": address,
            "state": state,
            "pincode": pincode
        })

        # Update student details in the database
        result = students_collection.update_one(
            {"_id": ObjectId(student_id)},
            {
                "$set": {
                    "fname": fname,
                    "lname": lname,
                    "email": email,
                    "phone_number": phone_number,
                    "address": address,
                    "state": state,
                    "pincode": pincode
                }
            }
        )

        # Check if the update operation was successful
        if result.modified_count == 1:
            # Redirect to /studentdetails upon successful update
            return redirect(url_for("studentdetails"))
        else:
            # If no documents were modified, return an error
            return jsonify({'error': 'No student found with the provided ID.'}), 404

    except Exception as e:
        # Log the error for debugging
        print("Error:", e)
        # Handle any errors
        return jsonify({'error': 'Failed to update student. Please try again.'}), 500


# Function to get student image data from MongoDB


def get_student_image_data(student_id):
    try:
        image_data = images_collection.find_one({'student_id': student_id})
        if image_data and 'imageData' in image_data:
            return image_data['imageData']
        else:
            return None
    except Exception as e:
        print(
            f'Error fetching student image data for student ID {student_id}: {str(e)}')
        return None


@app.route('/search_student', methods=['GET', 'POST'])
def search_student():
    if request.method == 'POST':
        # Get the search query from the form submission
        query = request.form.get('search_query', '')

        # Search for students in the database based on the query
        if query:
            results = students_collection.find({
                "$or": [
                    {"fname": {"$regex": query, "$options": "i"}},
                    {"lname": {"$regex": query, "$options": "i"}},
                    {"register": query}
                ]
            })

            # Convert MongoDB cursor to list of dictionaries
            students = list(results)

            # Render the template with the search results
            return render_template('searchstudent.html', results=students)
        else:
            # If no search query provided, render the template without search results
            return render_template('searchstudent.html')

    # If the request method is GET (initial page load), just render the template without search results
    else:
        # Return an empty list of results
        return render_template('searchstudent.html', results=[])

# Endpoint to get student details


@app.route('/get_student_details/<student_id>', methods=['GET'])
def get_student_details(student_id):
    try:
        # Find the student in the database using the provided student ID
        student = students_collection.find_one({'_id': ObjectId(student_id)})

        # Check if the student exists
        if student:
            # Return the student details as JSON response
            return jsonify(student), 200
        else:
            # If student not found, return a 404 error
            return jsonify({'error': 'Student not found'}), 404
    except Exception as e:
        # Return a 500 error if any exception occurs
        return jsonify({'error': str(e)}), 500

# Function to generate video frames


def generate_frames():
    # Open the video capture device (webcam)
    cap = cv2.VideoCapture(0)

    # Check if the camera opened successfully
    if not cap.isOpened():
        print("Error: Unable to open camera.")
        return

    while True:
        # Capture frame-by-frame
        ret, frame = cap.read()

        if not ret:
            break

        # Convert the frame to JPEG format
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        # Yield the frame in byte format
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    # Release the capture device
    cap.release()
    

def gen_frames(known_face_encodings , known_face_names):
    camera = cv2.VideoCapture(0)
    while True:
        success, frame = camera.read()  # read the camera frame
        if not success:
            break
        else:
            # Resize frame of video to 1/4 size for faster face recognition processing
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            # Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
            rgb_small_frame = small_frame[:, :, ::-1]

            # Only process every other frame of video to save time
        
            # Find all the faces and face encodings in the current frame of video
            face_locations = face_recognition.face_locations(rgb_small_frame)
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
            face_names = []
            for face_encoding in face_encodings:
                # See if the face is a match for the known face(s)
                matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
                name = "Unknown"
                # Or instead, use the known face with the smallest distance to the new face
                face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
                best_match_index = np.argmin(face_distances)
                if matches[best_match_index]:
                    name = known_face_names[best_match_index]
                    markAttendance(name, is_present=True) if is_name_in_list(name) else markAttendance(name, is_present=False)
                    update_last_recognition_time(name)
                face_names.append(name)

                            # Update attendance for students who are absent
            for name in student_names:
                if name not in face_names:
                    markAttendance(name, is_present=False)

            # Display the results
            for (top, right, bottom, left), name in zip(face_locations, face_names):
                # Scale back up face locations since the frame we detected in was scaled to 1/4 size
                top *= 4
                right *= 4
                bottom *= 4
                left *= 4

                # Draw a box around the face
                if name == "Unknown":
                    # If name is "Unknown", draw a red bounding box
                    cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
                    cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
                    font = cv2.FONT_HERSHEY_DUPLEX
                    cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)
                else:
                    # Otherwise, draw a green bounding box
                    cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                    cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 255, 0), cv2.FILLED)
                    font = cv2.FONT_HERSHEY_DUPLEX
                    cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)
                

            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            
# Define the path to the attendance CSV file
attendance_file = './attendance.csv'

# Check if the attendance CSV file exists, if not, create one with headers
if not os.path.exists(attendance_file):
    with open(attendance_file, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Name', 'Status', 'Date', 'Time'])

# Fetch student names from MongoDB collection
student_names = [student['fname'] for student in students_collection.find()]

# Dictionary to store the last recognition time for each student
last_recognition_times = {name: None for name in student_names}

def markAttendance(name, is_present=False):  # Default status is "Absent"
    attendance_file = "attendance.csv"

    current_datetime = datetime.now()
    date_str = current_datetime.strftime("%Y-%m-%d")
    time_str = current_datetime.strftime("%H:%M:%S")
    Status = "Present" if is_present else "Absent"

    file_exists = os.path.isfile(attendance_file)

    with open(attendance_file, mode='a+') as file:
        fieldnames = ['Name', 'Status', 'Date', 'Time']
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        file.seek(0)
        reader = csv.DictReader(file)
        entry_exists = False
        for row in reader:
            if row['Name'] == name and row['Date'] == date_str:
                entry_exists = True
                if row['Status'] == 'Absent' and is_present:
                    row['Status'] = 'Present'
                    row['Time'] = time_str
                    print("Name: ", name, "Status: ", Status, "Date: ", date_str, "Time: ", time_str)
                    break  # Break out of the loop since attendance has been marked
                elif row['Status'] == 'Present' and not is_present:
                    break  # Break out of the loop since attendance has been marked as absent
        if not entry_exists:
            print("Name: ", name, "Status: ", Status, "Date: ", date_str, "Time: ", time_str)
            writer.writerow({'Name': name, 'Status': Status, 'Date': date_str, 'Time': time_str})

def update_last_recognition_time(name):
    last_recognition_times[name] = datetime.now()

def is_name_in_list(name):
    return name in student_names
                
# Define a route for serving the video feed

@app.route('/video_feed')
def video_feed():

    images = images_collection.find()
    # # Convert bytes to PIL Image
    
    known_face_encodings=[]
    known_face_names = []
    
    for image in images:
        pil_image = Image.open(BytesIO(image['imageData']))
        student = students_collection.find_one({"register" : image['student_id']})
        image_np = np.array(pil_image)
        known_face_names.append(student['fname'])
        known_face_encodings.append(face_recognition.face_encodings(image_np)[0])


    # Return the response as a streaming response
    return Response(gen_frames(known_face_encodings , known_face_names), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/download/attendance')
def download():
    return send_file('./attendance.csv' , download_name='attendance.csv' , as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
