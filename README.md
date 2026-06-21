# 🎓 Student Task Manager System

A modern web-based **Student Task Management System** built using **Python Flask**, **SQLite**, **HTML/CSS**, **JavaScript**, and **Chart.js**. The system helps students and teachers manage tasks, attendance, files, and reports efficiently.

---

# 📌 Project Description

The Student Task Manager System is designed to simplify academic management by providing a centralized platform for:

* Task management
* Attendance management
* File upload and download
* Progress tracking
* Analytics dashboard
* Report generation
* Cloud deployment

This project demonstrates **Full Stack Development**, **Database Management**, **Cloud Computing**, and **DevOps practices**.

---

# 🚀 Features

## 🔐 Authentication System

* User Registration
* Secure Login
* Password Hashing
* Session Management
* Logout System

---

## 👨‍🎓 Student Features

* Dashboard
* Add Tasks
* Edit Tasks
* Delete Tasks
* Task Progress Tracking
* Attendance View
* File Download
* Profile Management

---

## 👨‍🏫 Teacher Features

* Create and Manage Tasks
* Mark Attendance
* Upload Study Materials
* Generate Reports
* View Analytics

---

## 📅 Attendance Management

* Mark Student Attendance
* View Attendance Records
* Attendance Analytics

---

## 📊 Analytics Dashboard

* Total Tasks
* Completed Tasks
* Pending Tasks
* Task Priority Statistics
* Attendance Statistics
* Interactive Charts

---

## 📂 File Management

* Upload Files
* Download Files
* Store Study Materials
* Assignment Sharing

---

## 📄 Report Generation

* PDF Report Export
* Excel Report Export
* Task Reports
* Attendance Reports

---

# 🛠️ Technologies Used

| Technology     | Purpose             |
| -------------- | ------------------- |
| Python         | Backend Programming |
| Flask          | Web Framework       |
| SQLAlchemy     | ORM                 |
| SQLite         | Database            |
| HTML5          | Frontend            |
| CSS3           | Styling             |
| JavaScript     | Client-side Scripts |
| Chart.js       | Analytics Dashboard |
| Pandas         | Excel Reports       |
| OpenPyXL       | Excel Export        |
| ReportLab      | PDF Reports         |
| Git & GitHub   | Version Control     |
| AWS EC2        | Backend Hosting     |
| AWS S3         | Static Hosting      |
| GitHub Actions | CI/CD               |

---

# 📂 Project Structure

```text
StudentTaskManager/
│
├── app.py
├── requirements.txt
├── Procfile
├── README.md
├── .gitignore
├── uploads/
├── templates/
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   ├── tasks.html
│   ├── attendance.html
│   ├── analytics.html
│   ├── profile.html
│   └── reports.html
│
├── static/
│   ├── css/
│   ├── js/
│   └── images/
│
├── instance/
│   └── taskmanager.db
│
└── .github/
    └── workflows/
        └── deploy.yml
```

---

# ⚙️ Installation Guide

## Clone Repository

```bash
git clone https://github.com/yourusername/student-task-manager.git
cd student-task-manager
```

---

## Create Virtual Environment

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

### Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

---

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Run Application

```bash
python app.py
```

Open browser:

```text
http://127.0.0.1:5000
```

---

# Database Tables

## User Table

```text
id
username
email
password
role
department
course
```

---

## Task Table

```text
id
title
subject
description
priority
status
progress
due_date
user_id
```

---

## Attendance Table

```text
id
student_id
date
status
```

---

## File Table

```text
id
filename
uploaded_by
upload_date
```

---

# System Workflow

```text
Register
   ↓
Login
   ↓
Dashboard
   ↓
Task Management
   ↓
Attendance
   ↓
Analytics
   ↓
File Upload
   ↓
Report Generation
```

---

# Cloud Deployment

## Backend

* AWS EC2
* Gunicorn
* Nginx

## Frontend

* AWS S3 Static Website Hosting

## CI/CD

* GitHub Actions

---

# Security Features

✅ Password Hashing

✅ Session Management

✅ SQLAlchemy ORM

✅ Secure File Upload

✅ Authentication Checks

---

# Future Enhancements

* Email Notifications
* Google Login
* Docker Deployment
* REST API
* Mobile Application
* AI-based Performance Prediction
* Push Notifications

---

# Screenshots

Add screenshots of:

* Login Page
* Register Page
* Dashboard
* Tasks
* Attendance
* Analytics
* File Upload
* Reports

---

# Learning Outcomes

* Full Stack Development
* Flask Framework
* Database Management
* Cloud Deployment
* DevOps & CI/CD
* Report Generation
* Data Visualization

---

# Author

**Naveen**

B.Sc Computer Science (Cybersecurity)

GitHub:
https://github.com/yourusername

LinkedIn:
https://linkedin.com/in/yourprofile

---

# License

This project is developed for educational and academic purposes.

© 2026 Naveen. All Rights Reserved.
