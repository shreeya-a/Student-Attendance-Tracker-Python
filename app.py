from flask import Flask, render_template, request, flash, redirect, url_for, session
from models import db, User, Student, Attendance, bcrypt
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
import os



app = Flask(__name__)

# db config

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:postgres@localhost:5432/attendance_system'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "supersecretkey"

db.init_app(app)
bcrypt.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_admin(admin_id):
    return User.query.get(int(admin_id))

@app.route('/')
@login_required
def home():
    return render_template("index.html", user=current_user.username)


# Route: Register (One-time user registration)
@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = bcrypt.generate_password_hash(request.form["password"]).decode("utf-8")

        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for("login"))

    return render_template("register.html")


@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username, is_admin=True).first()

        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid credentials or not an admin!", "danger")

    return render_template("login.html")


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


@app.route('/dashboard')
@login_required
def dashboard():
    if not current_user.is_admin:
        return "Access Denied!", 403
    students = Student.query.all()
    return render_template("dashboard.html", students=students)



if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug = True)