import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

# to load .env variables
load_dotenv()

# email settings
SMTP_SERVER = "smtp.gmail.com"  
SMTP_PORT = 587
SENDER_EMAIL = os.getenv("SENDER_EMAIL") 
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD") 

def send_warning_email(student_email, student_name, attendance_percentage):
    """
    Sends a warning email to students with attendance below 70%.
    
    Args:
    - student_email (str): The email of the student.
    - student_name (str): The name of the student.
    - attendance_percentage (float): The student's attendance percentage.
    """
    subject = "⚠️ Low Attendance Warning!"
    body = f"""
    Dear {student_name},

    We have noticed that your attendance percentage is currently {attendance_percentage:.2f}%, 
    which is below the required threshold of 70%. 

    Please ensure to attend classes regularly to avoid any penalties.

    Regards, 
    Admin Team
    """

    # Create the email
    msg = MIMEMultipart()
    msg["From"] = SENDER_EMAIL
    msg["To"] = student_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        # Connect to SMTP server
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()  # Secure the connection
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, student_email, msg.as_string())
        server.quit()
        print(f"Email sent to {student_email}")
    
    except Exception as e:
        print(f"Failed to send email to {student_email}: {e}")
