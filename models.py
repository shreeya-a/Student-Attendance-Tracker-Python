from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import UserMixin
from sqlalchemy import event
from flask_bcrypt import Bcrypt

import os
from dotenv import load_dotenv

# to load .env variables
load_dotenv()

db = SQLAlchemy()
bcrypt = Bcrypt()

# Admin User Model
class User(db.Model, UserMixin):
    # __tablename__ = 'admin_list'
    
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(100), unique = True, nullable = False)
    password = db.Column(db.String(255), nullable = False)
    is_admin = db.Column(db.Boolean, default = True)
    
    
# Student Model
class Student(db.Model):
    # __tablename__ = 'student_list'
    
    id = db.Column(db.Integer, primary_key = True)
    # student_id = db.Column(db.String(20), unique=True, nullable=False)  # Custom ID
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    address = db.Column(db.Text, nullable=False)
    phone = db.Column(db.String(15), unique=True, nullable=False)
 
# for automatic student_id generation       
# @event.listens_for(Student, "before_insert")
# def generate_student_id(mapper, connection, target):
#     """Auto-generate student_id before inserting a record"""
#     last_student = db.session.query(Student).order_by(Student.id.desc()).first()
#     next_id = last_student.id + 1 if last_student else 1  # Get the next available ID
#     target.student_id = f"STD{next_id:04d}"  # STD0001

class Attendance(db.Model):
    
    # __tablename__ = 'attendance_records'
    
    id = db.Column(db.Integer, primary_key = True)
    student_id = db.Column(db.Integer(), db.ForeignKey("student.id"), nullable = False)
    date = db.Column(db.Date, nullable = False)
    status = db.Column(db.String(10), nullable = False, default = datetime.utcnow().date)
    
# Function to create admin if not exists
def create_admin():
    with db.session.begin():  # Ensure atomic transactions
        admin_exists = User.query.filter_by(is_admin=True).first()
        if not admin_exists:
            admin_username = os.getenv("ADMIN_USERNAME")
            admin_password = os.getenv("ADMIN_PASSWORD")
            hashed_password = bcrypt.generate_password_hash(admin_password).decode("utf-8")

            admin = User(username=admin_username, password=hashed_password, is_admin=True)
            db.session.add(admin)
            print("✅ Admin user created successfully!")