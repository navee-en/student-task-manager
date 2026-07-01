from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
import calendar
from datetime import date
from flask import redirect
import os
from werkzeug.utils import secure_filename
import pandas as pd
from flask import send_file
from flask import send_from_directory
from reportlab.pdfgen import canvas
import boto3



app = Flask(__name__)

# ===========================
# AWS S3 Configuration
# ===========================

S3_BUCKET = "student-task-manager-navee"   # Replace with your bucket name

s3 = boto3.client("s3")

app.secret_key = "studenttaskmanager"

UPLOAD_FOLDER = 'uploads'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

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
# REGISTER
# ======================

@app.route('/create-account', methods=['POST'])
def create_account():

    existing_user = User.query.filter_by(
        email=request.form['email']
    ).first()

    if existing_user:
        return "Email already exists."

    hashed_password = generate_password_hash(
        request.form['password']
    )

    

    new_user = User(
       username=request.form['username'],
       email=request.form['email'],
       password=generate_password_hash(
        request.form['password']
       ),
      department=request.form['department'],
      course=request.form['course'],
      role=request.form['role']
    )
       

    db.session.add(new_user)
    db.session.commit()

    return redirect('/login')


# ======================
# LOGIN
# ======================

@app.route('/authenticate', methods=['POST'])
def login():

    username = request.form['username']
    password = request.form['password']

    user = User.query.filter_by(
        username=username
    ).first()

    if user and check_password_hash(
        user.password,
        password
    ):

        session['user_id'] = user.id
        session['role'] = user.role

        if user.role == "Admin":
            return redirect('admin') 
        
        elif user.role == "Teacher":
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

    student_count = User.query.count()

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
# STUDENTS
# ======================

@app.route('/students')
def students():

    students = User.query.all()

    return render_template(
        'students.html',
        students=students
    )

#================================
#ATTENDANCE
#================================

@app.route('/attendance')
def attendance():

    records = Attendance.query.all()

    students = User.query.all()

    return render_template(
        'attendance.html',

        records=records,

        students=students
    )

#=======================
# MARK-ATTENDANCE
#=======================

@app.route('/mark-attendance',
           methods=['POST'])
def mark_attendance():

    attendance = Attendance(

        student_id=request.form['student_id'],

        date=date.today(),

        status=request.form['status']
    )

    db.session.add(attendance)

    db.session.commit()

    return redirect('/attendance')

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
@app.route('/upload',methods=['POST'])
def upload():

  file = request.files['file']

  filename = secure_filename(file.filename)

  s3.upload_fileobj(
     file,
     S3_BUCKET,
     f"uploads/{filename}"
  )

  file_url = f"https://{S3_BUCKET}.s3.amazonaws.com/uploads/{filename}"
   

        new_file = File(
            filename=filename,
            uploaded_by=session['user_id'],
            upload_date=date.today()
        )

        db.session.add(new_file)
        db.session.commit()

    return redirect('/files')

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

@app.route('/profile')
def profile():

    user = User.query.get(
        session.get('user_id')
    )

    return render_template(
        'profile.html',
        user=user
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
