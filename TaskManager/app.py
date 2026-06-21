from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
import calendar
from datetime import date
from flask import redirect
import os
from werkzeug.utils import secure_filename


app = Flask(__name__)

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
       

    db.session.add(User)
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

@app.route('/teacher')
def teacher():

    if session.get('role') != 'Teacher':
        return redirect('/login')

    students = User.query.filter_by(
        role='Student'
    ).all()

    total_students = len(students)

    total_tasks = Task.query.count()

    return render_template(
        'teacher_dashboard.html',
        students=students,
        total_students=total_students,
        total_tasks=total_tasks
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

    return render_template(
        'reports.html'
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

    if file:

        filename = secure_filename(
            file.filename
        )

        file.save(
            os.path.join(
                app.config['UPLOAD_FOLDER'],
                filename
            )
        )

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

    return send_from_directory(
        app.config['UPLOAD_FOLDER'],
        filename,
        as_attachment=True
    )

#-------------PDF REPORT ROUTE--------------#

@app.route('/report/pdf')
def pdf_report():

    pdf = canvas.Canvas(
        "task_report.pdf"
    )

    pdf.drawString(
        100,
        800,
        "Student Task Report"
    )

    y = 760

    tasks = Task.query.all()

    for task in tasks:

        pdf.drawString(
            100,
            y,
            f"{task.title} - {task.status}"
        )

        y -= 20

    pdf.save()

    return send_file(
        "task_report.pdf",
        as_attachment=True
    )

#------------------EXCEL REPORT ROUTE---------------#

@app.route('/report/excel')
def excel_report():

    tasks = Task.query.all()

    data = []

    for task in tasks:

        data.append({
            'Title': task.title,
            'Subject': task.subject,
            'Priority': task.priority,
            'Status': task.status
        })

    df = pd.DataFrame(data)

    df.to_excel(
        'task_report.xlsx',
        index=False
    )

    return send_file(
        'task_report.xlsx',
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