import os
from flask import Flask, render_template, request, flash, redirect, url_for
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from dotenv import load_dotenv  # Load environment variables
from models import db, User, Student, Attendance, bcrypt, create_admin

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Use environment variables for config
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URI")
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

@app.route("/dashboard")
@login_required
def dashboard():
    if not current_user.is_admin:
        return "Access Denied!", 403
    students = Student.query.all()
    return render_template("dashboard.html", students=students)


@app.route('/add_student', methods=["GET", "POST"])
@login_required
def add_student():
    if request.method == "POST":
        name = request.form["name"]
        student_id = request.form["student_id"]
        email = request.form["email"]
        address = request.form["address"]
        phone = request.form["phone"]

        new_student = Student(student_id=student_id, name=name, email=email, address=address, phone=phone)
        db.session.add(new_student)
        db.session.commit()
        
        flash("Student added successfully!", "success")
        return redirect(url_for("dashboard"))
    
    return render_template("student/add_student.html")





if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        create_admin()  
    app.run(debug=True)
