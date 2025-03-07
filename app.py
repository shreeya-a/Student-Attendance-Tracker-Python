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
import io
import base64
import csv
from warning_email import send_warning_email


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
    student_statistics = []
    for student_id, stats in student_attendance.items():
        total = stats["Total"]
        student = Student.query.get(student_id)
        if total > 0:
            student_percentages[student_id] = {
                "Present": round((stats["Present"] / total) * 100, 2),
                "Absent": round((stats["Absent"] / total) * 100, 2),
                "Late": round((stats["Late"] / total) * 100, 2),
            }
        else:
            student_percentages[student_id] = {"Present": 0, "Absent": 0, "Late": 0}

        # Prepare student statistics for template
        student_statistics.append({
            "student_id": student.student_id,
            "first_name": student.first_name,
            "last_name": student.last_name,
            "present": stats["Present"],
            "absent": stats["Absent"],
            "late": stats["Late"]
        })

    print("Today's Attendance Summary:", today_attendance_summary)  # Debugging

    return render_template(
        "dashboard.html",
        total_students=total_students,
        today_attendance=today_attendance_summary,  # Pass today's attendance data
        daily_attendance=daily_attendance,
        student_percentages=student_percentages,
        student_statistics=student_statistics,
    )


# display student list in table

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
        student.first_name = request.form['first_name'].strip().capitalize()
        student.last_name = request.form['last_name'].strip().capitalize()
        student.email = request.form['email']
        student.phone = request.form['phone']
        student.address = request.form['address'].strip().capitalize()
        
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


@app.route('/overall-attendance-chart')
def overall_attendance_chart():
    daily_data = Attendance.query.with_entities(Attendance.date, Attendance.status).all()

    # Organize data
    dates = sorted(set(record.date for record in daily_data))[-10:]
    present_counts = [sum(1 for record in daily_data if record.date == date and record.status == "Present") for date in dates]
    absent_counts = [sum(1 for record in daily_data if record.date == date and record.status == "Absent") for date in dates]
    late_counts = [sum(1 for record in daily_data if record.date == date and record.status == "Late") for date in dates]

    # Plot Stacked Bar Chart
    fig, ax = plt.subplots(figsize=(10, 6.5))
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


@app.route('/download_csv')
@login_required
def download_csv():
    students = Student.query.all()
    attendance_records = Attendance.query.all()

    output = []
    headers = ["Student Name"] + sorted(set(a.date.strftime('%Y-%m-%d') for a in attendance_records)) + ["Total Present", "Total Absent", "Total Late"]

    # Build attendance data
    student_data = {s.id: {"name": f"{s.first_name} {s.last_name}", "attendance": {}} for s in students}

    for record in attendance_records:
        student_data[record.student_id]["attendance"][record.date.strftime('%Y-%m-%d')] = record.status

    for s_id, data in student_data.items():
        row = [data["name"]]
        total_present = total_absent = total_late = 0

        for date in headers[1:-3]:
            status = data["attendance"].get(date, "N/A")
            row.append(status)
            if status == "Present":
                total_present += 1
            elif status == "Absent":
                total_absent += 1
            elif status == "Late":
                total_late += 1

        row.extend([total_present, total_absent, total_late])
        output.append(row)

    # Generate CSV response
    si = io.StringIO()
    writer = csv.writer(si)
    writer.writerow(headers)
    writer.writerows(output)

    response = Response(si.getvalue(), mimetype="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=attendance_report.csv"
    return response


# Send warning to student with <70% attendance

def check_and_send_emails():
    with app.app_context():
        students = Student.query.all()

        for student in students:
            total_days = Attendance.query.filter_by(student_id=student.id).count()
            present_days = Attendance.query.filter_by(student_id=student.id, status="Present").count()

            if total_days > 0:
                attendance_percentage = (present_days / total_days) * 100

                if attendance_percentage < 70:
                    # Check if an email was sent in the last 1 days
                    recent_email = EmailLog.query.filter(
                        EmailLog.student_id == student.id,
                        EmailLog.sent_at >= datetime.utcnow() - timedelta(days=1)
                    ).first()

                    if not recent_email:
                        student_name = f"{student.first_name} {student.last_name}"
                        send_warning_email(student.email, student_name, attendance_percentage)

                        # Log the email sent
                        email_log = EmailLog(student_id=student.id)
                        db.session.add(email_log)
                        db.session.commit()


@app.route('/run-email-check')
@login_required
def run_email_check():
    check_and_send_emails()
    flash("Email check is running in the background!", "info")
    return redirect(url_for("dashboard"))



if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        create_admin()  
    # check_and_send_emails()

    app.run(debug=True, threaded = False)

