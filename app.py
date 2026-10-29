from flask import Flask, render_template, request, redirect, session, flash, url_for
from functools import wraps
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, date
import calendar
import os
import pandas as pd
from flask import send_file
from flask import send_from_directory
from reportlab.pdfgen import canvas
import boto3
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import re
import uuid
import smtplib
from email.message import EmailMessage
from datetime import timedelta

def validate_password(password):

    if len(password) < 12:
        return False, "Password must be at least 12 characters."

    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least 1 uppercase letter."

    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least 1 lowercase letter."

    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least 1 number."

    if not re.search(r'[^A-Za-z0-9]', password):
        return False, "Password must contain at least 1 special character."

    return True, ""



app = Flask(__name__)

limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"]
)

# ===========================
# AWS S3 Configuration
# ===========================

S3_BUCKET = "student-task-manager-navee-n7k4"
AWS_REGION = "ap-south-1"

s3 = boto3.client(
    "s3",
    region_name=AWS_REGION
)

app.secret_key = os.environ["SECRET_KEY"]

UPLOAD_FOLDER = 'uploads'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 3 * 1024 * 1024

db = SQLAlchemy(app)

#EMAIL CONFIGURATION

def send_email(to_email, subject, body):
    """Send one email using Gmail SMTP."""
    sender = os.environ.get("EMAIL_ADDRESS")
    app_password = os.environ.get("EMAIL_APP_PASSWORD")

    if not sender or not app_password:
        app.logger.error("Gmail email credentials are not configured.")
        return False

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = sender
    message["To"] = to_email
    message.set_content(body)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=20) as smtp:
            smtp.login(sender, app_password)
            smtp.send_message(message)

        return True

    except Exception:
        app.logger.exception("Email delivery failed.")
        return False

# ======================
# USER MODEL
# ======================

class User(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    email = db.Column(
        db.String(120),
        unique=True,
        nullable=False
    )

    password = db.Column(
        db.String(255),
        nullable=False
    )

    role = db.Column(
        db.String(20),
        default="Student"
    )

    department = db.Column(
        db.String(100)
    )

    course = db.Column(
        db.String(100)
    )

    # Student academic details
    registration_number = db.Column(
        db.String(50),
        unique=True,
        nullable=True
    )

    semester = db.Column(db.String(20))
    academic_year = db.Column(db.String(20))

    # Teacher professional details
    faculty_id = db.Column(
        db.String(50),
        unique=True,
        nullable=True
    )

    qualification = db.Column(db.String(150))
    designation = db.Column(db.String(100))

    # Store the S3 object key, not a public image URL
    profile_image_key = db.Column(db.String(500))


# ======================
# ROLE-BASED ACCESS CONTROL
# ======================

def role_required(*allowed_roles):

    def decorator(f):

        @wraps(f)
        def decorated_function(*args, **kwargs):

            # User must be logged in
            if 'user_id' not in session:
                return redirect(url_for('login_page'))

            # Get current user
            user = User.query.get(session['user_id'])

            # User must exist
            if not user:
                session.clear()
                return redirect(url_for('login_page'))

            # Check role
            if user.role not in allowed_roles:
                flash("Access denied. You do not have permission to access this page.", "error")
                return redirect(url_for('dashboard'))

            return f(*args, **kwargs)

        return decorated_function

    return decorator

# ======================
# TASK MODEL
# ======================

class Task(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    student_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id')
    )

    title = db.Column(
        db.String(200),
        nullable=False
    )

    subject = db.Column(
        db.String(100)
    )

    description = db.Column(
        db.Text
    )

    priority = db.Column(
        db.String(50),
        default="Medium"
    )

    status = db.Column(
        db.String(50),
        default="Pending"
    )

    progress = db.Column(
        db.Integer,
        default=0
    )

    due_date = db.Column(
        db.Date
    )

    created_date = db.Column(
        db.Date,
        default=date.today
    )

    teacher_id = db.Column(
      db.Integer,
      db.ForeignKey('user.id')
    )

    reminder_day_before_sent = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )

    reminder_due_date_sent = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )

#=============================
#Attendance model
#=============================

class Attendance(db.Model):
    __tablename__ = "attendance"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id')
    )
    date = db.Column(
        db.Date,
        default=date.today
    )
    status = db.Column(db.String(20))
    role = db.Column(
        db.String(20),
        default="Student"
    )

#========================
#MATERIAL
#========================

class Material(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    title = db.Column(
        db.String(200)
    )

    filename = db.Column(
        db.String(300)
    )

    teacher_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id')
    )

#==========================
#FILE MODELS
#==========================

class File(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    filename = db.Column(
        db.String(300),
        nullable=False
    )

    file_url = db.Column(
        db.String(500)
    )

    uploaded_by = db.Column(
        db.Integer,
        db.ForeignKey('user.id')
    )

    upload_date = db.Column(
        db.Date
    )


with app.app_context():
    db.create_all()
# ======================
# HOME
# ======================

@app.route('/')
def home():
    return redirect('/login')


# ======================
# LOGIN PAGE
# ======================

@app.route('/login')
def login_page():

    return render_template(
        'login.html'
    )


# ======================
# REGISTER PAGE
# ======================

@app.route('/register')
def register_page():

    return render_template(
        'register.html'
    )

# ======================
# ADMIN TEST ROUTE
# ======================

@app.route('/admin-test')
@role_required("Admin")
def admin_test():

    return """
        <h1>ADMIN ACCESS GRANTED</h1>
        <p>RBAC is working successfully.</p>
    """

# ======================
# REGISTER
# ======================

@app.route('/create-account', methods=['GET','POST'])
@limiter.limit("5 per hour")
def create_account():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        department = request.form.get('department')
        course = request.form.get('course')
        role = request.form.get('role')

        #never allow admin to be created though public registration
        if role =="Admin":
            role = "Student"

        # Check if username already exists
        existing_username = User.query.filter_by(username=username).first()
        if existing_username:
            flash("Username already exists. Please choose another username.", "error")
            return redirect(url_for("create_account"))

        # Check if email already exists
        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            flash("Email already registered. Please use another email.", "error")
            return redirect(url_for("create_account"))

        valid, message = validate_password(password)
        if not valid:
            flash(message, "error")
            return redirect(url_for("create_account"))

        # Create new user
        hashed_password = generate_password_hash(password)
        new_user = User(
            username=username,
            email=email,
            password=hashed_password,
            department=department,
            course=course,
            role=role
        )

        db.session.add(new_user)
        db.session.commit()

        return redirect('/login')

    return render_template('register.html')


# ======================
# LOGIN
# ======================
@app.route('/authenticate', methods=['GET','POST'])
@limiter.limit("10 per hour")
def login():

    username = request.form['username']
    password = request.form['password']

    user = User.query.filter_by(username=username).first()

    if user and check_password_hash(user.password, password):

        session['user_id'] = user.id
        session['role'] = user.role

        if user.role == "Teacher":
            return redirect('/teacher')
        else:
            return redirect('/dashboard')

    return "Invalid Login"
# ======================
# DASHBOARD
# ======================

@app.route('/dashboard')
def dashboard():


    if 'user_id' not in session:
        return redirect('/')

    tasks = Task.query.all()

    total_tasks = len(tasks)

    completed_tasks = len(
        [t for t in tasks
         if t.status == "Completed"]
    )

    pending_tasks = len(
        [t for t in tasks
         if t.status == "Pending"]
    )

    student_count = User.query.filter_by(role="Student").count()

    if total_tasks > 0:

        completion_percentage = int(
            (completed_tasks / total_tasks) * 100
        )

    else:

        completion_percentage = 0

    return render_template(

        'dashboard.html',

        total_tasks=total_tasks,

        completed_tasks=completed_tasks,

        pending_tasks=pending_tasks,

        student_count=student_count,

        completion_percentage=completion_percentage
    )

#---------------------TEACHERS DASHBOARD ROUTE---------------#

@app.route("/teacher")
def teacher():

    total_students = User.query.filter_by(role="Student").count()

    total_tasks = Task.query.count()

    completed_tasks = Task.query.filter_by(status="Completed").count()

    pending_tasks = Task.query.filter_by(status="Pending").count()

    return render_template(
        "teacher_dashboard.html",
        total_students=total_students,
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        pending_tasks=pending_tasks
    )

# ======================
# TASKS
# ======================

@app.route('/tasks')
def tasks():

    search = request.args.get('search', '')

    subject = request.args.get('subject', '')

    query = Task.query

    if search:

        query = query.filter(
            Task.title.contains(search)
        )

    if subject:

        query = query.filter_by(
            subject=subject
        )

    all_tasks = query.all()

    subjects = db.session.query(
        Task.subject
    ).distinct().all()

    return render_template(

        'tasks.html',

        tasks=all_tasks,

        subjects=subjects
    )

@app.route("/teacher/assign-task", methods=["GET", "POST"])
@role_required("Teacher")
def assign_task():
    students = User.query.filter_by(
        role="Student"
    ).order_by(User.username.asc()).all()

    if request.method == "POST":
        student_id = request.form.get("student_id", type=int)
        title = request.form.get("title", "").strip()
        subject = request.form.get("subject", "").strip()
        description = request.form.get("description", "").strip()
        priority = request.form.get("priority", "Medium")
        due_date_text = request.form.get("due_date", "")

        student = User.query.filter_by(
            id=student_id,
            role="Student"
        ).first()

        if not student or not title or not due_date_text:
            flash("Select a student and enter a title and due date.", "error")
            return redirect(url_for("assign_task"))

        if priority not in ("Low", "Medium", "High"):
            flash("Select a valid priority.", "error")
            return redirect(url_for("assign_task"))

        try:
            due_date = datetime.strptime(
                due_date_text, "%Y-%m-%d"
            ).date()
        except ValueError:
            flash("Please enter a valid due date.", "error")
            return redirect(url_for("assign_task"))

        task = Task(
            student_id=student.id,
            teacher_id=session["user_id"],
            title=title,
            subject=subject,
            description=description,
            priority=priority,
            status="Pending",
            progress=0,
            due_date=due_date
        )

        db.session.add(task)
        db.session.commit()

        email_sent = send_email(
            student.email,
            f"New task assigned: {title}",
            f"""Hello {student.username},

Your teacher has assigned you a new task.

Task: {title}
Subject: {subject or "Not specified"}
Description: {description or "No description provided"}
Priority: {priority}
Deadline: {due_date.strftime("%d %B %Y")}

Please log in to your Student Task Management System to review the task.

Regards,
Student Task Management System
"""
        )

        if email_sent:
            flash("Task assigned and email notification sent.", "success")
        else:
            flash(
                "Task assigned, but the email could not be sent. "
                "Check the server logs and Gmail configuration.",
                "error"
            )

        return redirect(url_for("assign_task"))

    return render_template(
        "teacher_assign_task.html",
        students=students
    )

@app.route("/teacher/announcements", methods=["GET", "POST"])
@role_required("Teacher")
def teacher_announcements():
    students = User.query.filter_by(
        role="Student"
    ).order_by(User.username.asc()).all()

    if request.method == "POST":
        subject = request.form.get("subject", "").strip()
        body = request.form.get("body", "").strip()
        recipient_mode = request.form.get("recipient_mode", "all")

        if not subject or not body:
            flash("Enter both a subject and a message.", "error")
            return redirect(url_for("teacher_announcements"))

        if len(subject) > 200 or len(body) > 10000:
            flash("The subject or message is too long.", "error")
            return redirect(url_for("teacher_announcements"))

        if recipient_mode == "all":
            recipients = students
        elif recipient_mode == "selected":
            selected_ids = request.form.getlist("student_ids")
            selected_ids = [
                int(value) for value in selected_ids
                if value.isdigit()
            ]

            recipients = User.query.filter(
                User.id.in_(selected_ids),
                User.role == "Student"
            ).all() if selected_ids else []
        else:
            recipients = []

        if not recipients:
            flash("Select at least one student.", "error")
            return redirect(url_for("teacher_announcements"))

        sent = 0
        failed = 0

        for student in recipients:
            if send_email(student.email, subject, body):
                sent += 1
            else:
                failed += 1

        if failed == 0:
            flash(f"Announcement emailed to {sent} student(s).", "success")
        else:
            flash(
                f"Sent: {sent}. Failed: {failed}. Check server logs.",
                "error"
            )

        return redirect(url_for("teacher_announcements"))

    return render_template(
        "teacher_announcements.html",
        students=students
    )


# ======================
# ADD TASK
# ======================

@app.route('/add-task', methods=['POST'])
def add_task():

    due_date = datetime.strptime(
        request.form['due_date'],
        '%Y-%m-%d'
    ).date()

    task = Task(

        student_id=session.get('user_id'),

        title=request.form['title'],

        subject=request.form['subject'],

        description=request.form['description'],

        priority=request.form['priority'],

        status="Pending",

        progress=0,

        due_date=due_date
    )

    db.session.add(task)

    db.session.commit()

    return redirect('/tasks')


# ======================
# COMPLETE TASK
# ======================

@app.route('/complete-task/<int:id>')
def complete_task(id):

    task = Task.query.get_or_404(id)

    task.status = "Completed"

    task.progress = 100

    db.session.commit()

    return redirect('/tasks')


# ======================
# DELETE TASK
# ======================

@app.route('/delete-task/<int:id>')
def delete_task(id):

    task = Task.query.get_or_404(id)

    db.session.delete(task)

    db.session.commit()

    return redirect('/tasks')


# ======================
# EDIT TASK
# ======================

@app.route('/edit-task/<int:id>',
           methods=['GET', 'POST'])
def edit_task(id):

    task = Task.query.get_or_404(id)

    if request.method == 'POST':

        task.title = request.form['title']
        task.subject = request.form['subject']
        task.description = request.form['description']
        task.priority = request.form['priority']
        task.status = request.form['status']
        task.progress = request.form['progress']

        db.session.commit()

        return redirect('/tasks')

    return render_template(
        'edit_task.html',
        task=task
    )

# ======================
# UPDATE TASK
# ======================

@app.route(
    '/update-task/<int:id>',
    methods=['POST']
)
def update_task(id):

    task = Task.query.get_or_404(id)

    task.title = request.form['title']

    task.subject = request.form['subject']

    task.priority = request.form['priority']

    task.progress = int(
        request.form['progress']
    )

    db.session.commit()

    return redirect('/tasks')


# ======================
# ANALYTICS
# ======================

@app.route('/analytics')
def analytics():

    total_tasks = Task.query.count()

    completed_tasks = Task.query.filter_by(
        status='Completed'
    ).count()

    pending_tasks = Task.query.filter_by(
        status='Pending'
    ).count()

    high_priority = Task.query.filter_by(
        priority='High'
    ).count()

    medium_priority = Task.query.filter_by(
        priority='Medium'
    ).count()

    low_priority = Task.query.filter_by(
        priority='Low'
    ).count()

    present_students = Attendance.query.filter_by(
        status='Present'
    ).count()

    absent_students = Attendance.query.filter_by(
        status='Absent'
    ).count()

    return render_template(
        'analytics.html',
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        pending_tasks=pending_tasks,
        high_priority=high_priority,
        medium_priority=medium_priority,
        low_priority=low_priority,
        present_students=present_students,
        absent_students=absent_students
    )

# ======================
# CALENDAR
# ======================

@app.route('/calendar')
def calendar_page():

    current_year = datetime.now().year

    current_month = datetime.now().month

    cal = calendar.monthcalendar(
        current_year,
        current_month
    )

    tasks = Task.query.all()

    return render_template(
        'calendar.html',

        cal=cal,

        tasks=tasks,

        month=current_month,

        year=current_year
    )


# ======================
# REPORTS
# ======================

@app.route('/reports')
def reports():

    tasks = Task.query.all()

    return render_template(
        "reports.html",
        tasks=tasks
    )

# ======================
# STUDENTS — STUDENT ACCOUNTS ONLY
# ======================

@app.route('/students')
@role_required("Teacher", "Admin")
def students():
    students = User.query.filter_by(
        role="Student"
    ).order_by(User.username.asc()).all()

    return render_template(
        'students.html',
        students=students
    )

# ================================
# ATTENDANCE VIEW
# ================================

@app.route('/attendance')
@role_required("Student", "Teacher", "Admin")
def attendance():
    records = Attendance.query.all()
    students = User.query.filter_by(role="Student").all()

    return render_template(
        'attendance.html',
        records=records,
        students=students
    )


# ================================
# MARK ATTENDANCE - TEACHER ONLY
# ================================

@app.route('/mark-attendance', methods=['POST'])
@role_required("Teacher")
def mark_attendance():
    student_id = request.form.get('student_id')
    status = request.form.get('status')

    if not student_id or status not in ("Present", "Absent"):
        flash("Please select a valid student and attendance status.", "error")
        return redirect(url_for('attendance'))

    student = User.query.filter_by(
        id=student_id,
        role="Student"
    ).first()

    if not student:
        flash("Student account not found.", "error")
        return redirect(url_for('attendance'))

    attendance_record = Attendance(
        student_id=student.id,
        date=date.today(),
        status=status
    )

    db.session.add(attendance_record)
    db.session.commit()

    flash("Attendance marked successfully.", "success")
    return redirect(url_for('attendance'))


#============================
# FILE UPLOAD
#============================

@app.route('/files')
def files():

    files = File.query.all()

    return render_template(
        'files.html',
        files=files
    )

#---------------------UPLOADS-------------------------#
@app.route('/upload', methods=['POST'])
def upload():

    try:
        file = request.files.get('file')

        if not file:
            return "No file", 400

        user_id = session.get('user_id')

        if not user_id:
            return "Login required", 401

        filename = secure_filename(file.filename)

        # Upload to S3
        s3.upload_fileobj(file, S3_BUCKET, f"uploads/{filename}")

        # Save in DB
        new_file = File(
            filename=filename,
            uploaded_by=user_id,
            upload_date=date.today()
        )

        db.session.add(new_file)
        db.session.commit()

        return "UPLOAD SUCCESS"

    except Exception as e:
        return str(e), 500
#------------------------ DOWNLOAD THE REPORT----------------#
@app.route('/download/<filename>')
def download(filename):

     url = s3.generate_presigned_url(
         'get_object',
         Params={
            'Bucket': S3_BUCKET,
            'Key': f"uploads/{filename}"
         },
         ExpiresIn=3600
     )

     return redirect(url)

#-------------PDF REPORT ROUTE--------------#

@app.route('/report/pdf')
def pdf_report():

    pdf_path = os.path.join(
        "reports",
        "task_report.pdf"
    )

    pdf = canvas.Canvas(pdf_path)

    pdf.setTitle("Student Task Report")

    pdf.setFont("Helvetica-Bold",18)

    pdf.drawString(
        180,
        800,
        "Student Task Report"
    )

    pdf.setFont("Helvetica",12)

    y = 760

    tasks = Task.query.all()

    for task in tasks:

        pdf.drawString(
            50,
            y,
            f"Title : {task.title}"
        )

        pdf.drawString(
            250,
            y,
            f"Status : {task.status}"
        )

        pdf.drawString(
            430,
            y,
            f"Priority : {task.priority}"
        )

        y -= 25

        if y < 60:

            pdf.showPage()

            y = 760

    pdf.save()

    return send_file(
        pdf_path,
        as_attachment=True
    )

#------------------EXCEL REPORT ROUTE---------------#

@app.route('/report/excel')
def excel_report():

    tasks = Task.query.all()

    data = []

    for task in tasks:

        data.append({

            "Title": task.title,

            "Subject": task.subject,

            "Priority": task.priority,

            "Status": task.status

        })

    df = pd.DataFrame(data)

    excel_path = os.path.join(
        "reports",
        "task_report.xlsx"
    )

    df.to_excel(
        excel_path,
        index=False
    )

    return send_file(
        excel_path,
        as_attachment=True
    )


#=======================
# PROFILE
# ======================

@app.route('/profile', methods=['GET', 'POST'])
@role_required("Student", "Teacher", "Admin")
def profile():
    user = User.query.get_or_404(session['user_id'])

    if request.method == 'POST':
        # Keep the user's existing account role unchanged.
        if user.role == "Student":
            registration_number = (
                request.form.get('registration_number', '').strip()
                or None
            )

            if registration_number:
                existing = User.query.filter(
                    User.registration_number == registration_number,
                    User.id != user.id
                ).first()

                if existing:
                    flash("That registration number is already in use.", "error")
                    return redirect(url_for('profile'))

            user.registration_number = registration_number
            user.semester = request.form.get('semester', '').strip() or None
            user.academic_year = (
                request.form.get('academic_year', '').strip() or None
            )

        elif user.role == "Teacher":
            faculty_id = request.form.get('faculty_id', '').strip() or None

            if faculty_id:
                existing = User.query.filter(
                    User.faculty_id == faculty_id,
                    User.id != user.id
                ).first()

                if existing:
                    flash("That faculty ID is already in use.", "error")
                    return redirect(url_for('profile'))

            user.faculty_id = faculty_id
            user.qualification = (
                request.form.get('qualification', '').strip() or None
            )
            user.designation = (
                request.form.get('designation', '').strip() or None
            )

        # Optional profile photo
        photo = request.files.get('profile_picture')

        if photo and photo.filename:
            allowed_types = {
                'image/jpeg': 'jpg',
                'image/png': 'png',
                'image/webp': 'webp'
            }

            extension = photo.filename.rsplit('.', 1)[-1].lower()
            content_type = photo.mimetype

            if (
                '.' not in photo.filename
                or extension not in {'jpg', 'jpeg', 'png', 'webp'}
                or content_type not in allowed_types
            ):
                flash("Upload a JPG, PNG, or WebP image.", "error")
                return redirect(url_for('profile'))

            # Read at most 3 MB + 1 byte to check the actual file size.
            image_data = photo.read(3 * 1024 * 1024 + 1)

            if not image_data or len(image_data) > 3 * 1024 * 1024:
                flash("The image must be no larger than 3 MB.", "error")
                return redirect(url_for('profile'))

            # Use a unique object key to avoid overwriting another file.
            ext = allowed_types[content_type]
            object_key = (
                f"profile-pictures/{user.id}/{uuid.uuid4().hex}.{ext}"
            )

            try:
                from io import BytesIO

                s3.upload_fileobj(
                    BytesIO(image_data),
                    S3_BUCKET,
                    object_key,
                    ExtraArgs={'ContentType': content_type}
                )

                user.profile_image_key = object_key

            except Exception:
                app.logger.exception("Profile picture upload failed")
                flash("Photo upload failed. Check your AWS S3 permissions.", "error")
                return redirect(url_for('profile'))

        db.session.commit()
        flash("Profile updated successfully.", "success")
        return redirect(url_for('profile'))

    profile_image_url = None

    if user.profile_image_key:
        try:
            profile_image_url = s3.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': S3_BUCKET,
                    'Key': user.profile_image_key
                },
                ExpiresIn=3600
            )
        except Exception:
            app.logger.exception("Could not create profile image URL")

    return render_template(
        'profile.html',
        user=user,
        profile_image_url=profile_image_url
    )


# ======================
# LOGOUT
# ======================

@app.route('/logout')
def logout():

    session.clear()

    return redirect('/')


# ======================
# RUN APP
# ======================

if __name__ == "__main__":

    app.run(
        debug=True
    )