import os
from flask import Flask, render_template, request, flash, redirect, url_for
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from dotenv import load_dotenv  # Load environment variables
from models import db, User, Student, Attendance, bcrypt, create_admin

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

@app.route("/dashboard")
@login_required
def dashboard():
    if not current_user.is_admin:
        return "Access Denied!", 403
    students = Student.query.all()
    return render_template("dashboard.html", students=students)


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
        


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        create_admin()  
    app.run(debug=True)
