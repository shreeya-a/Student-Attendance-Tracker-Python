import os
from flask import Flask, render_template, request, flash, redirect, url_for, send_file, Response
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from dotenv import load_dotenv  # Load environment variables
from models import db, User, Student, Attendance, bcrypt, create_admin, EmailLog
from datetime import datetime, timedelta
import matplotlib
matplotlib.use("Agg")  # Use a non-GUI backend
import matplotlib.pyplot as plt
import io
import base64
from collections import defaultdict
import csv
from warning_email import send_warning_email

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Use environment variables for config
app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///attendance_system.db'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

# Initialize database and bcrypt
db.init_app(app)
bcrypt.init_app(app)

# Initialize Flask-Login
login_manager = LoginManager(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_admin(admin_id):
    return User.query.get(int(admin_id))

@app.route("/")
def home():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username, is_admin=True).first()

        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            flash("Login successful!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid credentials or not an admin!", "danger")

    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

@app.route('/dashboard')
@login_required
def dashboard():
    today_date = datetime.today().date()
    total_students = Student.query.count()
    today_attendance_records = Attendance.query.filter_by(date=today_date).all()
    attendance_records = Attendance.query.all()
    
    daily_attendance = defaultdict(lambda: {"Present": 0, "Absent": 0, "Late": 0})
    student_attendance = defaultdict(lambda: {"Present": 0, "Absent": 0, "Late": 0, "Total": 0})

    for record in attendance_records:
        date = record.date.strftime("%Y-%m-%d")
        status = record.status
        daily_attendance[date][status] += 1
        student_attendance[record.student_id][status] += 1
        student_attendance[record.student_id]["Total"] += 1

    today_attendance_summary = {"Present": 0, "Absent": 0, "Late": 0}
    for record in today_attendance_records:
        today_attendance_summary[record.status] += 1

    student_statistics = []
    for student_id, stats in student_attendance.items():
        student = Student.query.get(student_id)
        if student:
            student_statistics.append({
                "student_id": student.student_id,
                "first_name": student.first_name,
                "last_name": student.last_name,
                "present": stats["Present"],
                "absent": stats["Absent"],
                "late": stats["Late"]
            })

    return render_template(
        "dashboard.html",
        total_students=total_students,
        today_attendance=today_attendance_summary,
        daily_attendance=daily_attendance,
        student_statistics=student_statistics,
    )

@app.route('/view-student', methods=["GET", "POST"])
@login_required
def view_student():
    if request.method == "POST":
        first_name = request.form["first_name"].strip().capitalize()
        last_name = request.form["last_name"].strip().capitalize()
        email = request.form["email"]
        address = request.form["address"].strip().capitalize()
        phone = request.form["phone"]

        new_student = Student(first_name=first_name, last_name=last_name, email=email, address=address, phone=phone)
        try:
            db.session.add(new_student)
            db.session.commit()
            flash("Student added successfully!", "success")
        except:
            flash("Error: Email or Phone number already exists!", "danger")
        
    students = Student.query.order_by(Student.first_name.asc()).all()
    return render_template("student/view_student.html", students=students)

@app.route('/update/<int:id>', methods=["GET", "POST"])
def update(id):
    student = Student.query.get_or_404(id)
    
    if request.method == 'POST':
        student.first_name = request.form['first_name'].strip().capitalize()
        student.last_name = request.form['last_name'].strip().capitalize()
        student.email = request.form['email']
        student.phone = request.form['phone']
        student.address = request.form['address'].strip().capitalize()
        
        try:
            db.session.commit()
            flash("Student details updated successfully!", "success")
            return redirect(url_for('view_student'))
        except:
            flash("Error: There was an issue updating student details!", "danger")
    
    return render_template('student/edit_student.html', student=student)

@app.route('/delete/<int:id>')
def delete(id):
    student = Student.query.get_or_404(id)
    
    try:
        db.session.delete(student)
        db.session.commit()
        flash("Student deleted successfully!", "success")
    except:
        flash("Error: There was an issue deleting the student details!", "danger")
    
    return redirect(url_for("view_student"))

@app.route('/mark-attendance', methods=["GET", "POST"])
def mark_attendance():
    students = Student.query.all()
    today_date = datetime.today().date()
    selected_date_str = request.args.get("date", today_date.strftime("%Y-%m-%d"))
    selected_date = datetime.strptime(selected_date_str, "%Y-%m-%d").date()
    attendance_records = {att.student_id: att.status for att in Attendance.query.filter_by(date=selected_date).all()}

    if request.method == "POST":
        form_date = datetime.strptime(request.form.get("date"), "%Y-%m-%d").date()
        if form_date > today_date:
            flash("You cannot mark attendance for a future date.", "danger")
            return redirect(url_for("mark_attendance", date=selected_date_str))

        for student in students:
            status = request.form.get(f"status_{student.id}")
            if status:
                existing_attendance = Attendance.query.filter_by(student_id=student.id, date=form_date).first()
                if existing_attendance:
                    existing_attendance.status = status
                else:
                    db.session.add(Attendance(student_id=student.id, date=form_date, status=status))
        db.session.commit()
        flash("Attendance marked successfully!", "success")
    
    return render_template("attendance/mark_attendance.html", students=students, selected_date=selected_date.strftime("%Y-%m-%d"), attendance_records=attendance_records)
