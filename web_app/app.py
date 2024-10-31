from flask import Flask, render_template, request, redirect, url_for
from pymysql import connections
import boto3
from config import *

app = Flask(__name__)

bucket = custombucket
region = customregion

db_conn = connections.Connection(
    host=customhost,
    port=3306,
    user=customuser,
    password=custompass,
    db=customdb
)

@app.route('/')
def index():
    # Render the main page with buttons to navigate to add or search for a student.
    return render_template('index.html')

@app.route('/add_student', methods=['GET', 'POST'])
def add_student():
    if request.method == 'POST':
        # Extract form data
        email = request.form['email']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        mobile = request.form['mobile']
        college = request.form['college']
        major = request.form['major']
        graduation_year = request.form['graduation_year']
        skills = request.form['skills']
        area_of_interest = request.form['area_of_interest']

        # Get the resume file
        resume = request.files['resume']
        resume_file_name_in_s3 = f"{email}_resume"

        # Insert details into the database
        cursor = db_conn.cursor()
        insert_sql = """
        INSERT INTO student (email, first_name, last_name, mobile, college, major, graduation_year, skills, area_of_interest)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        try:
            cursor.execute(insert_sql, (email, first_name, last_name, mobile, college, major, graduation_year, skills, area_of_interest))
            db_conn.commit()
        except Exception as e:
            cursor.close()
            return str(e), 500

        # Uploading resume to S3 bucket
        s3 = boto3.client('s3')
        try:
            s3.upload_fileobj(resume, bucket, resume_file_name_in_s3)
        except Exception as e:
            return str(e), 500

        # Success message
        cursor.close()
        return f"<div style='text-align: center; margin-top: 50px;'><h1>{first_name}'s details entered in our database successfully!</h1></div>"
    else:
        # If method is GET, show the add_student form
        return render_template('add_student.html')

@app.route('/search_student', methods=['GET', 'POST'])
def search_student():
    if request.method == 'POST':
        email = request.form['email']
        cursor = db_conn.cursor()
        search_sql = "SELECT * FROM student WHERE email = %s"
        cursor.execute(search_sql, (email,))
        student = cursor.fetchone()
        cursor.close()

        # Ensure 'student' is a dict with keys corresponding to your database columns
        if student:
            student_data = {
                'email': student[0],
                'first_name': student[1],
                'last_name': student[2],
                'mobile': student[3],
                'college': student[4],
                'major': student[5],
                'graduation_year': student[6],
                'skills': student[7],
                'area_of_interest': student[8],
            }
            return render_template('search_student.html', student=student_data)
        else:
            return render_template('search_student.html', error="No record found.")

    return render_template('search_student.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)  # Running on port 80 requires sudo privileges
