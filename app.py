import os
from flask import Flask, render_template, request, flash, redirect, url_for, send_file, Response
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from dotenv import load_dotenv  # Load environment variables
from models import db, User, Student, Attendance, bcrypt, create_admin
from datetime import datetime
import matplotlib
matplotlib.use("Agg")  # Use a non-GUI backend
import matplotlib.pyplot as plt
import io
import base64
from collections import defaultdict
import io
import base64
# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Use environment variables for config
# app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URI")
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///attendance_system.db'

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
    return redirect(url_for("dashboard"))  

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

# @app.route("/dashboard")
# @login_required
# def dashboard():
#     if not current_user.is_admin:
#         return "Access Denied!", 403
#     students = Student.query.all()
#     return render_template("dashboard.html", students=students)



from flask import render_template
from collections import defaultdict
from datetime import datetime
from models import Attendance, Student  # Ensure correct model import

@app.route('/dashboard')
@login_required
def dashboard():
    today_date = datetime.today().date()

    # Get total students
    total_students = Student.query.count()

    # Fetch only today's attendance records
    today_attendance_records = Attendance.query.filter_by(date=today_date).all()
    
    # Fetch all attendance records for historical data
    attendance_records = Attendance.query.all()

    # Initialize summary structures
    daily_attendance = defaultdict(lambda: {"Present": 0, "Absent": 0, "Late": 0})
    student_attendance = defaultdict(lambda: {"Present": 0, "Absent": 0, "Late": 0, "Total": 0})

    # Process all attendance records (for historical trends)
    for record in attendance_records:
        date = record.date.strftime("%Y-%m-%d")
        status = record.status

        # Count attendance per day
        daily_attendance[date][status] += 1

        # Count attendance per student
        student_attendance[record.student_id][status] += 1
        student_attendance[record.student_id]["Total"] += 1

    # Process only today's attendance records
    today_attendance_summary = {"Present": 0, "Absent": 0, "Late": 0}
    for record in today_attendance_records:
        today_attendance_summary[record.status] += 1

    # Calculate attendance percentage per student
    student_percentages = {}
    for student_id, stats in student_attendance.items():
        total = stats["Total"]
        if total > 0:
            student_percentages[student_id] = {
                "Present": round((stats["Present"] / total) * 100, 2),
                "Absent": round((stats["Absent"] / total) * 100, 2),
                "Late": round((stats["Late"] / total) * 100, 2),
            }
        else:
            student_percentages[student_id] = {"Present": 0, "Absent": 0, "Late": 0}

    print("Today's Attendance Summary:", today_attendance_summary)  # Debugging

    return render_template(
        "dashboard.html",
        total_students=total_students,
        today_attendance=today_attendance_summary,  # Pass today's attendance data
        daily_attendance=daily_attendance,
        student_percentages=student_percentages,
    )




# @app.route('/add_student', methods=["GET", "POST"])
# @login_required
# def add_student():
#     if request.method == "POST":
#         first_name = request.form["first_name"]
#         last_name = request.form["last_name"]
#         email = request.form["email"]
#         address = request.form["address"]
#         phone = request.form["phone"]

#         new_student = Student(first_name= first_name, last_name = last_name, email=email, address=address, phone=phone)
#         db.session.add(new_student)
#         db.session.commit()
        
#         flash("Student added successfully!", "success")
#         return redirect(url_for("student/view_student.html"))
    
#     return render_template("student/add_student.html")

# display student list in table

@app.route('/view-student', methods=["GET", "POST"])
@login_required
def view_student():
    if request.method == "POST":
        first_name = request.form["first_name"]
        last_name = request.form["last_name"]
        email = request.form["email"]
        address = request.form["address"]
        phone = request.form["phone"]

        new_student = Student(first_name=first_name, last_name=last_name, email=email, address=address, phone=phone)
        try:
            
            db.session.add(new_student)
            db.session.commit()
            
            flash("Student added successfully!", "success")
            # return redirect(url_for("view_student")) 
        except Exception as e:
            flash("Error: Email or Phone number already exists!", "danger")
            # return redirect("view_student") 
            return redirect(url_for("student/view_student.html"))
        
    
    students = Student.query.order_by(Student.first_name.asc()).all()  
    return render_template("student/view_student.html", students=students)


# update  student details

@app.route('/update/<int:id>', methods = ["GET", "POST"])
def update(id):
    student = Student.query.get_or_404(id)
    
    if request.method == 'POST':
        student.first_name = request.form['first_name']
        student.last_name = request.form['last_name']
        student.email = request.form['email']
        student.phone = request.form['phone']
        student.address = request.form['address']
        
        try:
            db.session.commit()
            flash("Student details updated successfully!", "success")
            return redirect(url_for('view_student'))

        except Exception as e:
            flash(f"Error: There was an issue while updating student details! {e}", "danger")
    else:
        return render_template('student/edit_student.html', student = student)

# delete student details
@app.route('/delete/<int:id>')
def delete(id):
    student = Student.query.get_or_404(id)
    
    try:
        db.session.delete(student)
        db.session.commit()
        flash("Student deleted successfully!", "success")
        return redirect(url_for("view_student")) 
    except:
        flash(f"Error: There was an issue while deleting the student details!", "danger")
        return redirect(url_for('view_student'))
        


# #Attendance


@app.route('/mark-attendance', methods=["GET", "POST"])
def mark_attendance():
    students = Student.query.all()
    today_date = datetime.today().date()

    # Get selected date from GET request (if present), otherwise default to today
    selected_date_str = request.args.get("date", today_date.strftime("%Y-%m-%d"))
    selected_date = datetime.strptime(selected_date_str, "%Y-%m-%d").date()

    # Fetch attendance records for the selected date
    attendance_records = {att.student_id: att.status for att in Attendance.query.filter_by(date=selected_date).all()}

    if request.method == "POST":
        form_date_str = request.form.get("date")
        if not form_date_str:
            flash("Please select a valid date.", "danger")
            return redirect(url_for("mark_attendance", date=selected_date_str))

        form_date = datetime.strptime(form_date_str, "%Y-%m-%d").date()
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
                    new_attendance = Attendance(student_id=student.id, date=form_date, status=status)
                    db.session.add(new_attendance)

        db.session.commit()
        flash("Attendance marked successfully!", "success")
        return redirect(url_for("mark_attendance", date=form_date.strftime("%Y-%m-%d")))

    return render_template(
        "attendance/mark_attendance.html",
        students=students,
        today_date=today_date,
        selected_date=selected_date.strftime("%Y-%m-%d"),
        attendance_records=attendance_records
    )




# view attendance records


@app.route('/attendance-records', methods=['GET', 'POST'])
def attendance_records():
    students = Student.query.all()
    attendance_data = {}
    
    # Handle both GET and POST requests
    selected_date = request.form.get('date') if request.method == 'POST' else request.args.get('date')
    today_date = datetime.today().strftime('%Y-%m-%d')

    # Default to today's date if no date is selected
    date_to_query = selected_date if selected_date else today_date
    records = Attendance.query.filter_by(date=date_to_query).all()

    # Store attendance records per student
    for student in students:
        attendance_data[student] = [record for record in records if record.student_id == student.id]

    return render_template('attendance/attendance_records.html', 
                           students=students, 
                           attendance_data=attendance_data, 
                           selected_date=selected_date or today_date,
                           today_date=today_date)


# Attendance chart 


# Attendance chart for pie chart

@app.route('/attendance-chart')
def attendance_chart():
    # Fetch attendance data
    attendance_records = Attendance.query.all()

    # Aggregate data
    present = sum(1 for record in attendance_records if record.status == "Present")
    absent = sum(1 for record in attendance_records if record.status == "Absent")
    late = sum(1 for record in attendance_records if record.status == "Late")

    # Generate Pie Chart
    labels = ["Present", "Absent", "Late"]
    values = [present, absent, late]
    colors = ["green", "red", "yellow"]

    fig = plt.figure(figsize=(6, 4))
    plt.pie(values, labels=labels, autopct='%1.1f%%', colors=colors, startangle=140)
    plt.title("Overall Attendance Distribution")

    # Save chart to a BytesIO object
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plt.close(fig)
    return send_file(img, mimetype='image/png')


# Attendance chart for daily records

@app.route('/daily-attendance-chart')
def daily_attendance_chart():
    daily_data = Attendance.query.with_entities(Attendance.date, Attendance.status).all()

    # Organize data
    dates = sorted(set(record.date for record in daily_data))
    present_counts = [sum(1 for record in daily_data if record.date == date and record.status == "Present") for date in dates]
    absent_counts = [sum(1 for record in daily_data if record.date == date and record.status == "Absent") for date in dates]
    late_counts = [sum(1 for record in daily_data if record.date == date and record.status == "Late") for date in dates]

    # Plot Line Chart
    fig = plt.figure(figsize=(8, 5))
    plt.plot(dates, present_counts, label="Present", marker="o", color="green")
    plt.plot(dates, absent_counts, label="Absent", marker="o", color="red")
    plt.plot(dates, late_counts, label="Late", marker="o", color="yellow")
    plt.xlabel("Date")
    plt.ylabel("Number of Students")
    plt.title("Daily Attendance Trends")
    plt.legend()

    # Save and send chart
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plt.close(fig)
    
    return send_file(img, mimetype='image/png')


# Show student performance chart
@app.route('/student-performance-chart')
def student_performance_chart():
    colors = []
    students = Student.query.all()
    student_attendance = {student.id: {"Present": 0, "Absent": 0, "Late": 0, "Total": 0} for student in students}

    # Fetch attendance data
    for record in Attendance.query.all():
        student_attendance[record.student_id][record.status] += 1
        student_attendance[record.student_id]["Total"] += 1

    student_names = [f"{student.first_name} {student.last_name}" for student in students]
    present_percents = [
        round((student_attendance[student.id]["Present"] / student_attendance[student.id]["Total"]) * 100, 2)
        if student_attendance[student.id]["Total"] > 0 else 0
        for student in students
    ]
    colors = ["green" if percent > 90 else "orange" if percent < 60 else "lightblue" for percent in present_percents]   
                
    # Plot Bar Chart
    fig = plt.figure(figsize=(8,5))
    plt.bar(student_names, present_percents, color=colors)
    plt.xlabel("Students")
    plt.ylabel("Attendance %")
    plt.title("Student Performance (Attendance %)")
    plt.xticks(rotation=45)

    plt.tight_layout()

    # Save and send chart
    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches="tight")
    img.seek(0)
    plt.close(fig)

    return send_file(img, mimetype='image/png')


@app.route('/overall-attendance-chart')
def overall_attendance_chart():
    daily_data = Attendance.query.with_entities(Attendance.date, Attendance.status).all()

    # Organize data
    dates = sorted(set(record.date for record in daily_data))
    present_counts = [sum(1 for record in daily_data if record.date == date and record.status == "Present") for date in dates]
    absent_counts = [sum(1 for record in daily_data if record.date == date and record.status == "Absent") for date in dates]
    late_counts = [sum(1 for record in daily_data if record.date == date and record.status == "Late") for date in dates]

    # Plot Stacked Bar Chart
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(dates, present_counts, label="Present", color="green")
    ax.bar(dates, absent_counts, label="Absent", color="red", bottom=present_counts)
    ax.bar(dates, late_counts, label="Late", color="orange", bottom=[p + a for p, a in zip(present_counts, absent_counts)])
    
    plt.xlabel("Date")
    plt.ylabel("Number of Students")
    plt.title("Overall Class Attendance Statistics")
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()

    # Save and send chart
    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches="tight")
    img.seek(0)
    plt.close(fig)
    
    return send_file(img, mimetype='image/png')


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        create_admin()  
    app.run(debug=True, threaded = False)
