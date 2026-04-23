# Face Recognition Exam Hall Prediction System

A full-stack Flask application for student enrollment, biometric face template capture, and real-time exam hall prediction using facial recognition.

## Features
- **Student Management:** Secure CRUD operations for student registration.
- **Biometric Enrollment:** Multi-position face template capture (10 samples per student).
- **Training Pipeline:** Visual simulation of preprocessing, segmentation, and feature extraction.
- **Real-time Recognition:** High-performance threaded camera scanner for instant identification.
- **Attendance Tracking:** Automatic logging of recognized students with CSV export.
- **Optimized UI:** Responsive dashboard with modern aesthetics and auto-managed camera power.

## Prerequisites
- **Python 3.8+**
- **MySQL Server**
- **Webcam**

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/FRS-Exam-Hall-Prediction.git
   cd FRS-Exam-Hall-Prediction
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Database**
   - Create a MySQL database (e.g., `face_recognition`).
   - Run the SQL commands in `schema.sql` to create the required tables.

5. **Setup Environment Variables**
   Copy the example environment file and fill in your details:
   ```bash
   cp .env.example .env  # On Windows: copy .env.example .env
   ```
   Edit the `.env` file with your MySQL credentials and a secret key.


## Running the Application

```bash
python app.py
```
Open `http://127.0.0.1:5000` in your browser.

## How to use
1. **Login** as administrator.
2. **Register** a new student.
3. **Capture** 10 face positions (follow the on-screen guide).
4. **Train** the model (visual pipeline).
5. **Predict:** Use the scanner to identify students and assign exam halls.
6. **Export:** Download attendance reports from the Attendance dashboard.
