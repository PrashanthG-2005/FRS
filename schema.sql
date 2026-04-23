CREATE DATABASE IF NOT EXISTS face_prediction_db;
USE face_prediction_db;

CREATE TABLE IF NOT EXISTS students (
    id INT AUTO_INCREMENT PRIMARY KEY,
    reg_no VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    address TEXT,
    mobile VARCHAR(20),
    email VARCHAR(100),
    aadhar VARCHAR(20),
    department VARCHAR(100),
    year VARCHAR(20),
    exam_hall VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS attendance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    reg_no VARCHAR(50),
    name VARCHAR(100),
    date DATE,
    time TIME,
    status VARCHAR(20),
    FOREIGN KEY (reg_no) REFERENCES students(reg_no)
);

CREATE TABLE IF NOT EXISTS admin (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL
);

INSERT INTO admin (username, password) VALUES ('admin', 'admin123');
