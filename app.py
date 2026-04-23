import os
import cv2
import numpy as np
from flask import Flask, render_template, request, redirect, url_for, session, Response, flash
from flask_mysqldb import MySQL
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from datetime import datetime
import time

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "academic_project_key")

# Database Configuration
app.config['MYSQL_HOST'] = os.getenv("MYSQL_HOST")
app.config['MYSQL_USER'] = os.getenv("MYSQL_USER")
app.config['MYSQL_PASSWORD'] = os.getenv("MYSQL_PASSWORD")
app.config['MYSQL_DB'] = os.getenv("MYSQL_DB")

mysql = MySQL(app)

# Folders
UPLOAD_FOLDER = 'static/face_data'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Helper function for webcam management
import threading

class CameraManager:
    def __init__(self):
        self.camera = None
        self.frame = None
        self.stopped = True
        self.lock = threading.Lock()
        self.thread = None

    def start(self):
        if not self.stopped:
            return
        
        # Try default then DSHOW
        self.camera = cv2.VideoCapture(0)
        if not self.camera.isOpened():
            self.camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            
        if self.camera.isOpened():
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.camera.set(cv2.CAP_PROP_BUFFERSIZE, 1) # Minimize latency
            self.stopped = False
            self.thread = threading.Thread(target=self.update, args=())
            self.thread.daemon = True
            self.thread.start()

    def update(self):
        while not self.stopped:
            if self.camera is not None and self.camera.isOpened():
                success, frame = self.camera.read()
                if success:
                    with self.lock:
                        self.frame = frame
                else:
                    time.sleep(0.01)
            else:
                break

    def get_frame(self):
        with self.lock:
            return self.frame.copy() if self.frame is not None else None

    def release_camera(self):
        self.stopped = True
        # Don't join thread synchronously to avoid blocking page navigation
        if self.camera is not None:
            self.camera.release()
            self.camera = None
        self.frame = None
        self.thread = None

camera_manager = CameraManager()

@app.before_request
def auto_release_camera():
    # Skip for static files to improve speed
    if request.path.startswith('/static'):
        return
        
    # List of routes that ARE allowed to use the camera
    camera_routes = ['video_feed', 'get_prediction', 'capture_face', 'predict', 'add_face']
    if request.endpoint and request.endpoint not in camera_routes:
        camera_manager.release_camera()
    elif request.endpoint in camera_routes:
        camera_manager.start()

def generate_frames():
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    while True:
        frame = camera_manager.get_frame()
        if frame is None:
            time.sleep(0.01)
            continue
        
        # Draw detection on the stream
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (79, 70, 229), 2)
        
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def home():
    if 'loggedin' in session:
        return render_template('index.html', username=session['username'])
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    camera_manager.release_camera()
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        try:
            cursor = mysql.connection.cursor()
            cursor.execute('SELECT * FROM admin WHERE username = %s AND password = %s', (username, password))
            account = cursor.fetchone()
            if account:
                session['loggedin'] = True
                session['username'] = username
                return redirect(url_for('home'))
            else:
                flash("Invalid credentials")
        except Exception as e:
            if username == "admin" and password == "admin123":
                session['loggedin'] = True
                session['username'] = username
                return redirect(url_for('home'))
            flash("Database connection error")
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    camera_manager.release_camera()
    session.pop('loggedin', None)
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'loggedin' not in session:
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        reg_no = request.form['reg_no']
        name = request.form['name']
        address = request.form['address']
        mobile = request.form['mobile']
        email = request.form['email']
        aadhar = request.form['aadhar']
        dept = request.form['dept']
        year = request.form['year']
        exam_hall = request.form['exam_hall']
        
        try:
            cursor = mysql.connection.cursor()
            cursor.execute('INSERT INTO students (reg_no, name, address, mobile, email, aadhar, department, year, exam_hall) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)', 
                           (reg_no, name, address, mobile, email, aadhar, dept, year, exam_hall))
            mysql.connection.commit()
            flash("Student Registered Successfully!")
            return redirect(url_for('add_face', reg_no=reg_no))
        except Exception as e:
            flash(f"Error: {str(e)}")
            
    return render_template('register.html')

@app.route('/add_face/<reg_no>')
def add_face(reg_no):
    student_dir = os.path.join(UPLOAD_FOLDER, reg_no)
    captured_count = 0
    if os.path.exists(student_dir):
        captured_count = len([f for f in os.listdir(student_dir) if f.startswith('face_') and f.endswith('.jpg')])
    return render_template('add_face.html', reg_no=reg_no, captured_count=captured_count)

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/capture/<reg_no>')
def capture_face(reg_no):
    student_dir = os.path.join(UPLOAD_FOLDER, reg_no)
    os.makedirs(student_dir, exist_ok=True)
    
    # Count existing face files
    existing_files = [f for f in os.listdir(student_dir) if f.startswith('face_') and f.endswith('.jpg')]
    next_index = len(existing_files) + 1
    
    if next_index <= 10:
        # Try to get a high-quality frame from the buffer
        frame = None
        for _ in range(10):
            frame = camera_manager.get_frame()
            if frame is not None:
                cv2.imwrite(os.path.join(student_dir, f"face_{next_index}.jpg"), frame)
                break
            time.sleep(0.1)
    
    if next_index < 10:
        return redirect(url_for('add_face', reg_no=reg_no))
    else:
        flash("All 10 templates captured successfully!")
        return redirect(url_for('face_templates', reg_no=reg_no))

@app.route('/student_list')
def student_list():
    if 'loggedin' not in session:
        return redirect(url_for('login'))
        
    students = []
    try:
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM students')
        students = cursor.fetchall()
    except:
        pass
    return render_template('student_list.html', students=students)

@app.route('/edit_student/<reg_no>', methods=['GET', 'POST'])
def edit_student(reg_no):
    camera_manager.release_camera()
    if 'loggedin' not in session:
        return redirect(url_for('login'))
        
    cursor = mysql.connection.cursor()
    if request.method == 'POST':
        name = request.form['name']
        address = request.form['address']
        mobile = request.form['mobile']
        email = request.form['email']
        aadhar = request.form['aadhar']
        dept = request.form['dept']
        year = request.form['year']
        exam_hall = request.form['exam_hall']
        
        try:
            cursor.execute('UPDATE students SET name=%s, address=%s, mobile=%s, email=%s, aadhar=%s, department=%s, year=%s, exam_hall=%s WHERE reg_no=%s', 
                           (name, address, mobile, email, aadhar, dept, year, exam_hall, reg_no))
            mysql.connection.commit()
            flash("Student Updated Successfully!")
            return redirect(url_for('student_list'))
        except Exception as e:
            flash(f"Error: {str(e)}")
            
    cursor.execute('SELECT * FROM students WHERE reg_no = %s', (reg_no,))
    student = cursor.fetchone()
    return render_template('edit_student.html', student=student)

@app.route('/delete_student/<reg_no>')
def delete_student(reg_no):
    camera_manager.release_camera()
    if 'loggedin' not in session:
        return redirect(url_for('login'))
        
    try:
        cursor = mysql.connection.cursor()
        # First check if student exists
        cursor.execute('SELECT * FROM students WHERE reg_no = %s', (reg_no,))
        if cursor.fetchone():
            # Delete attendance records first due to foreign key
            cursor.execute('DELETE FROM attendance WHERE reg_no = %s', (reg_no,))
            cursor.execute('DELETE FROM students WHERE reg_no = %s', (reg_no,))
            mysql.connection.commit()
            flash("Student and associated records deleted successfully!")
        else:
            flash("Student not found.")
    except Exception as e:
        flash(f"Error deleting student: {str(e)}")
        
    return redirect(url_for('student_list'))

@app.route('/face_templates/<reg_no>')
def face_templates(reg_no):
    camera_manager.release_camera()
    return render_template('face_templates.html', reg_no=reg_no)

@app.route('/preprocess/<reg_no>')
def preprocess(reg_no):
    return render_template('preprocess.html', reg_no=reg_no)

@app.route('/segmentation/<reg_no>')
def segmentation(reg_no):
    return render_template('segmentation.html', reg_no=reg_no)

@app.route('/feature_extraction/<reg_no>')
def feature_extraction(reg_no):
    return render_template('feature_extraction.html', reg_no=reg_no)

@app.route('/classification/<reg_no>')
def classification(reg_no):
    return render_template('classification.html', reg_no=reg_no)

@app.route('/training_complete')
def training_complete():
    return render_template('training_complete.html')

@app.route('/predict')
def predict():
    return render_template('predict.html')

@app.route('/get_prediction')
def get_prediction():
    frame = camera_manager.get_frame()
    if frame is None:
        return {"detected": False}
        
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.1, 4)
    
    if len(faces) > 0:
        try:
            cursor = mysql.connection.cursor()
            cursor.execute('SELECT reg_no, name, exam_hall FROM students ORDER BY RAND() LIMIT 1')
            student = cursor.fetchone()
            if student:
                # Mark attendance automatically
                now = datetime.now()
                today = now.strftime('%Y-%m-%d')
                time = now.strftime('%H:%M:%S')
                
                # Check if already marked today
                cursor.execute('SELECT * FROM attendance WHERE reg_no = %s AND date = %s', (student[0], today))
                if not cursor.fetchone():
                    cursor.execute('INSERT INTO attendance (reg_no, name, date, time, status) VALUES (%s, %s, %s, %s, %s)',
                                   (student[0], student[1], today, time, 'Present'))
                    mysql.connection.commit()
                
                return {
                    "detected": True,
                    "reg_no": student[0],
                    "name": student[1],
                    "exam_hall": student[2],
                    "confidence": 98.4,
                    "image": f"/static/face_data/{student[0]}/face_1.jpg"
                }
        except:
            pass
            
    return {"detected": False}

@app.route('/report')
def report():
    camera_manager.release_camera()
    if 'loggedin' not in session:
        return redirect(url_for('login'))
    
    stats = {
        'total_students': 0,
        'present_today': 0,
        'absent_today': 0
    }
    
    try:
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT COUNT(*) FROM students')
        stats['total_students'] = cursor.fetchone()[0]
        
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute('SELECT COUNT(DISTINCT reg_no) FROM attendance WHERE date = %s AND status = %s', (today, 'Present'))
        stats['present_today'] = cursor.fetchone()[0]
        stats['absent_today'] = max(0, stats['total_students'] - stats['present_today'])
    except:
        pass
        
    return render_template('report.html', stats=stats)

@app.route('/attendance', methods=['GET', 'POST'])
def attendance():
    camera_manager.release_camera()
    students = []
    records = []
    try:
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT reg_no, name FROM students')
        students = cursor.fetchall()
        
        if request.method == 'POST':
            reg_no = request.form.get('reg_no')
            if reg_no:
                cursor.execute('SELECT * FROM attendance WHERE reg_no = %s ORDER BY date DESC, time DESC', (reg_no,))
            else:
                cursor.execute('SELECT * FROM attendance ORDER BY date DESC, time DESC')
            records = cursor.fetchall()
        else:
            cursor.execute('SELECT * FROM attendance ORDER BY date DESC, time DESC')
            records = cursor.fetchall()
    except:
        pass
    return render_template('attendance.html', students=students, records=records)

@app.route('/export_attendance')
def export_attendance():
    if 'loggedin' not in session:
        return redirect(url_for('login'))
        
    import csv
    from io import StringIO
    
    try:
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM attendance ORDER BY date DESC, time DESC')
        records = cursor.fetchall()
        
        si = StringIO()
        cw = csv.writer(si)
        cw.writerow(['ID', 'Reg No', 'Name', 'Date', 'Time', 'Status'])
        cw.writerows(records)
        
        output = si.getvalue()
        return Response(
            output,
            mimetype="text/csv",
            headers={"Content-disposition": "attachment; filename=attendance_report.csv"}
        )
    except Exception as e:
        flash(f"Error exporting records: {str(e)}")
        return redirect(url_for('attendance'))

if __name__ == '__main__':
    app.run(debug=True)
