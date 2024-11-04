attendance_file = 'attendance.csv'

@app.route('/mark_attendance', methods=['POST'])
def mark_attendance():
    if request.method == 'POST':
        # Get student ID from the form
        student_id = request.form.get('fname') 

        # Open the attendance CSV file in append mode
        with open(attendance_file, 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)

            # Check if the CSV file header exists, write it if not
            if csvfile.tell() == 0:
                writer.writerow(['Student Name', 'Status', 'Time'])

            # Retrieve student name from MongoDB using the ID
            try:
                student_data = students_collection.find_one({'_id': ObjectId(student_id)})
                if student_data:
                    student_name = student_data['fname']
                else:
                    student_name = "Unknown (ID not found)"
            except Exception as e:
                print(f'Error retrieving student name: {str(e)}')
                student_name = "Error (retrieving name)"

            # You may need to get frame and known_face_encodings from somewhere
            frame = None  # Provide the frame data
            known_face_encodings = None  # Provide the known face encodings data
            known_face_names = None  # Provide the known face names data

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            small_frame = cv2.resize(rgb_frame, (0, 0), fx=0.25, fy=0.25)  # Adjust scaling factor as needed

            # Find all faces and their encodings in the current video frame
            face_locations = face_recognition.face_locations(small_frame)
            face_encodings = face_recognition.face_encodings(small_frame, face_locations)

            students_present = []
            attendance_history = {}  # Dictionary to track last seen time for recognized students

            for face_encoding in face_encodings:
                name = "Unknown"
                matches = face_recognition.compare_faces(known_face_encodings, face_encoding)

                # Check for matches and update attendance history
                if True in matches:
                    first_match_index = matches.index(True)
                    name = known_face_names[first_match_index]

                    # Update attendance history for the recognized student
                    current_time = datetime.now()
                    attendance_history[name] = current_time

                # Check for absence based on time threshold (optional)
                if name in attendance_history:
                    time_since_last_seen = (datetime.now() - attendance_history[name]).total_seconds() / 60  # Convert to minutes
                    if time_since_last_seen > 10:  # Adjust threshold in minutes as needed
                        # Mark student as absent (you can implement logic to update a separate database/CSV for absence)
                        print(f"{name} is marked absent after {time_since_last_seen:.2f} minutes")

                        # Optionally, remove from attendance_history if considered absent
                        # del attendance_history[name]

                    students_present.append(name)

                    # Get current time
                    current_time = datetime.now().strftime("%H:%M:%S")

                    # Write attendance data to CSV
                    writer.writerow([student_name, "Present", current_time])
                    
            # CSV generation
            csv_data = "Student Name, Status, Time"
            # Set the appropriate content type for CSV
            response = Response(csv_data, mimetype='text/csv')
            # Set Content-Disposition header to prompt download
            response.headers['Content-Disposition'] = 'attachment; filename=attendance.csv'
            
            return response

    # Handle if method is not POST
    return jsonify({'error': 'Invalid request method'}), 400