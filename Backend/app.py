from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file, jsonify
from flask_socketio import SocketIO
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
from datetime import timedelta
import sqlite3
import os
from utils.ai_processor import analyze_complaint
from utils.pdf_highlighter import highlight_pdf
from utils.ai_dashboard_assistant import AIDashboardAssistant
from models.database_models import init_db, get_db_connection

# Import notice services
from utils.notice_service import NoticeService, NOTICE_TYPES
from utils.file_handler import FileHandler

# Import notification services
from utils.notification_service import NotificationService, NOTIFICATION_TYPES
from utils.websocket_handler import WebSocketHandler

# Import assignment services
from utils.assignment_service import AssignmentService, RewardType

# Import event services
from utils.event_service import EventService, EventType, TargetAudience
from utils.email_service import EmailService

app = Flask(__name__)

# CRITICAL: Fixed SECRET_KEY - DO NOT change this or all sessions will be invalidated
# In production, use environment variable: os.environ.get('SECRET_KEY', 'fallback-key')
app.config['SECRET_KEY'] = 'academic_grievance_system_fixed_secret_key_2024_do_not_change'

# Session Configuration - Prevent automatic logout
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)  # 1 hour session lifetime
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent JavaScript access to session cookie
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF protection
app.config['SESSION_REFRESH_EACH_REQUEST'] = True  # Auto-refresh session on each request

# Upload Configuration
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ANSWER_SHEETS_FOLDER'] = 'static/uploads/answer_sheets'
app.config['ASSIGNMENTS_FOLDER'] = 'static/uploads/assignments'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['ALLOWED_EXTENSIONS'] = {'pdf'}

# Initialize SocketIO with threading for Python 3.13 compatibility
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode='threading',
    logger=True,
    engineio_logger=False
)

# Ensure upload directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['ANSWER_SHEETS_FOLDER'], exist_ok=True)
os.makedirs(app.config['ASSIGNMENTS_FOLDER'], exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'highlighted'), exist_ok=True)

# Initialize database
init_db()

# ============================================================================
# WEBSOCKET EVENT HANDLERS
# ============================================================================

@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection"""
    return WebSocketHandler.handle_connect(socketio)

@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection"""
    WebSocketHandler.handle_disconnect()

@socketio.on('authenticate')
def handle_authenticate(data):
    """Handle WebSocket authentication"""
    return WebSocketHandler.handle_authenticate(data)

# ============================================================================
# SESSION AND AUTHENTICATION
# ============================================================================

# Session refresh handler - Keeps session alive on each request
@app.before_request
def refresh_session():
    """
    Refresh session on each request to prevent automatic logout.
    This extends the session lifetime on every page visit and ensures
    session.permanent is always True for logged-in users.
    """
    if 'user_id' in session:
        session.permanent = True  # Ensure permanent session is always set
        session.modified = True  # Mark session as modified to refresh expiry

# Helper function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Login required decorators
def student_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('user_type') != 'student':
            flash('Please login as student to access this page', 'error')
            return redirect(url_for('student_login'))
        return f(*args, **kwargs)
    return decorated_function

def faculty_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('user_type') != 'faculty':
            flash('Please login as faculty to access this page', 'error')
            return redirect(url_for('faculty_login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('user_type') != 'admin':
            flash('Please login as admin to access this page', 'error')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/student/register', methods=['GET', 'POST'])
def student_register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not all([name, email, password]):
            flash('All fields are required', 'error')
            return redirect(url_for('student_register'))
        
        conn = get_db_connection()
        try:
            conn.execute(
                'INSERT INTO students (name, email, password_hash) VALUES (?, ?, ?)',
                (name, email, generate_password_hash(password))
            )
            conn.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('student_login'))
        except sqlite3.IntegrityError:
            flash('Email already exists', 'error')
        finally:
            conn.close()
    
    return render_template('student_register.html')

@app.route('/student/login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        conn = get_db_connection()
        student = conn.execute('SELECT * FROM students WHERE email = ?', (email,)).fetchone()
        conn.close()
        
        if student and check_password_hash(student['password_hash'], password):
            session.permanent = True  # Enable permanent session (1 hour lifetime)
            session['user_id'] = student['id']
            session['user_type'] = 'student'
            session['user_name'] = student['name']
            return redirect(url_for('student_dashboard'))
        else:
            flash('Invalid credentials', 'error')
    
    return render_template('student_login.html')

@app.route('/faculty/login', methods=['GET', 'POST'])
def faculty_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        conn = get_db_connection()
        faculty = conn.execute('SELECT * FROM faculty WHERE email = ?', (email,)).fetchone()
        conn.close()
        
        if faculty and check_password_hash(faculty['password_hash'], password):
            session.permanent = True  # Enable permanent session (1 hour lifetime)
            session['user_id'] = faculty['id']
            session['user_type'] = 'faculty'
            session['user_name'] = faculty['name']
            session['faculty_subject'] = faculty['subject']
            return redirect(url_for('faculty_dashboard'))
        else:
            flash('Invalid credentials', 'error')
    
    return render_template('faculty_login.html')

@app.route('/faculty/register', methods=['GET', 'POST'])
def faculty_register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        subject = request.form.get('subject')
        department = request.form.get('department')
        employee_id = request.form.get('employee_id')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validation
        if not all([name, email, subject, department, employee_id, password, confirm_password]):
            flash('All fields are required', 'error')
            return redirect(url_for('faculty_register'))
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return redirect(url_for('faculty_register'))
        
        if len(password) < 6:
            flash('Password must be at least 6 characters', 'error')
            return redirect(url_for('faculty_register'))
        
        conn = get_db_connection()
        try:
            conn.execute(
                '''INSERT INTO faculty (name, email, subject, department, employee_id, password_hash) 
                   VALUES (?, ?, ?, ?, ?, ?)''',
                (name, email, subject, department, employee_id, generate_password_hash(password))
            )
            conn.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('faculty_login'))
        except sqlite3.IntegrityError as e:
            if 'email' in str(e):
                flash('Email already exists', 'error')
            elif 'employee_id' in str(e):
                flash('Employee ID already exists', 'error')
            else:
                flash('Registration failed. Please try again.', 'error')
        finally:
            conn.close()
    
    return render_template('faculty_register.html')

@app.route('/student/dashboard')
@student_login_required
def student_dashboard():
    student_id = session['user_id']
    conn = get_db_connection()
    
    # Get complaints
    complaints = conn.execute(
        'SELECT * FROM complaints WHERE student_id = ? ORDER BY id DESC',
        (student_id,)
    ).fetchall()
    
    # Get unread notice count
    unread_notice_count = NoticeService.get_unread_count(student_id)
    
    # Get AI-powered insights
    ai_insights = AIDashboardAssistant.get_student_insights(student_id, conn)
    
    conn.close()
    
    return render_template('student_dashboard.html', 
                         complaints=complaints,
                         unread_notice_count=unread_notice_count,
                         ai_insights=ai_insights)

@app.route('/student/results')
@student_login_required
def student_results():
    conn = get_db_connection()
    
    # Define max marks for each exam type
    exam_max_marks = {
        'Insem-1': 20,
        'Insem-2': 20,
        'End Sem': 60
    }
    
    # Fetch marks with faculty information and answer sheets
    # Only show published results
    results = conn.execute(
        '''SELECT m.*, f.name as faculty_name, a.pdf_path, a.id as answer_sheet_id,
                  rs.is_result_declared
           FROM marks m
           JOIN faculty f ON m.faculty_id = f.id
           LEFT JOIN answer_sheets a ON m.student_id = a.student_id 
               AND m.subject = a.subject AND m.exam = a.exam
           LEFT JOIN result_status rs ON m.exam = rs.exam
           WHERE m.student_id = ? AND (m.is_published = 1 OR rs.is_result_declared = 1)
           ORDER BY m.created_at DESC''',
        (session['user_id'],)
    ).fetchall()
    
    # Group results by exam
    exams_dict = {}
    for result in results:
        exam = result['exam']
        if exam not in exams_dict:
            exams_dict[exam] = {
                'exam': exam,
                'results': [],
                'is_declared': result['is_result_declared'] == 1 if result['is_result_declared'] is not None else False,
                'max_marks_per_subject': exam_max_marks.get(exam, 100)
            }
        exams_dict[exam]['results'].append(result)
    
    # Calculate totals and grades for each exam
    # Convert all marks to percentage out of 100
    for exam_data in exams_dict.values():
        max_marks_per_subject = exam_data['max_marks_per_subject']
        
        # Convert each subject's marks to out of 100
        total_percentage = 0
        for result in exam_data['results']:
            subject_percentage = (result['marks'] / max_marks_per_subject) * 100
            total_percentage += subject_percentage
        
        # Average percentage across all subjects
        num_subjects = len(exam_data['results'])
        average_percentage = total_percentage / num_subjects if num_subjects > 0 else 0
        
        # Calculate total marks (sum of actual marks obtained)
        total_marks = sum(r['marks'] for r in exam_data['results'])
        total_possible = num_subjects * max_marks_per_subject
        
        # Calculate grade based on average percentage
        if average_percentage >= 90:
            grade = 'A+'
        elif average_percentage >= 80:
            grade = 'A'
        elif average_percentage >= 70:
            grade = 'B+'
        elif average_percentage >= 60:
            grade = 'B'
        elif average_percentage >= 50:
            grade = 'C'
        elif average_percentage >= 40:
            grade = 'D'
        else:
            grade = 'F'
        
        exam_data['total_marks'] = total_marks
        exam_data['total_possible'] = total_possible
        exam_data['percentage'] = round(average_percentage, 2)
        exam_data['grade'] = grade
        exam_data['status'] = 'PASSED' if average_percentage >= 40 else 'FAILED'
    
    conn.close()
    
    return render_template('view_results.html', exams_dict=exams_dict, results=results)

@app.route('/student/complaint/new', methods=['GET', 'POST'])
@student_login_required
def new_complaint():
    
    if request.method == 'POST':
        subject = request.form.get('subject')
        exam = request.form.get('exam')
        complaint_text = request.form.get('complaint_text')
        
        if not all([subject, exam, complaint_text]):
            flash('All fields are required', 'error')
            return redirect(url_for('new_complaint'))
        
        conn = get_db_connection()
        
        # Check if answer sheet exists for this student, subject, and exam
        answer_sheet = conn.execute(
            'SELECT * FROM answer_sheets WHERE student_id = ? AND subject = ? AND exam = ?',
            (session['user_id'], subject, exam)
        ).fetchone()
        
        if not answer_sheet:
            flash('No answer sheet found for this subject and exam', 'error')
            conn.close()
            return redirect(url_for('new_complaint'))
        
        # Process complaint with AI
        ai_result = analyze_complaint(complaint_text)
        
        # Highlight PDF
        highlighted_path = None
        if answer_sheet['pdf_path'] and ai_result['question_number']:
            highlighted_path = highlight_pdf(
                answer_sheet['pdf_path'],
                ai_result['question_number']
            )
        
        # Insert complaint with all AI fields
        conn.execute(
            '''INSERT INTO complaints 
               (student_id, subject, exam, complaint_text, extracted_question, 
                ai_summary, ai_issue_type, ai_detailed_explanation, ai_confidence_score,
                highlighted_pdf_path, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (session['user_id'], subject, exam, complaint_text,
             ai_result['question_number'], ai_result['summary'],
             ai_result['issue_type'], ai_result['detailed_explanation'],
             ai_result['confidence_score'], highlighted_path, 'Pending Review')
        )
        conn.commit()
        conn.close()
        
        flash('Complaint submitted successfully!', 'success')
        return redirect(url_for('student_dashboard'))
    
    return render_template('complaint_form.html')

@app.route('/faculty/dashboard')
@faculty_login_required
def faculty_dashboard():
    conn = get_db_connection()
    
    # Get complaints
    complaints = conn.execute(
        '''SELECT c.*, s.name as student_name, s.email as student_email
           FROM complaints c
           JOIN students s ON c.student_id = s.id
           ORDER BY c.id DESC'''
    ).fetchall()
    
    # Get AI-powered insights
    faculty_id = session['user_id']
    ai_insights = AIDashboardAssistant.get_faculty_insights(faculty_id, conn)
    
    conn.close()
    
    return render_template('faculty_dashboard.html', 
                         complaints=complaints,
                         ai_insights=ai_insights)

@app.route('/faculty/add-marks', methods=['GET', 'POST'])
@faculty_login_required
def add_marks():
    conn = get_db_connection()
    
    if request.method == 'POST':
        student_id = request.form.get('student_id')
        subject = request.form.get('subject')
        exam = request.form.get('exam')
        marks = request.form.get('marks')
        
        # Validate inputs
        if not all([student_id, subject, exam, marks]):
            flash('All fields are required', 'error')
            students = conn.execute('SELECT * FROM students ORDER BY name').fetchall()
            conn.close()
            return render_template('add_marks.html', students=students)
        
        # Validate marks
        try:
            marks = int(marks)
            
            # Check max marks based on exam type
            max_marks_dict = {
                'Insem-1': 20,
                'Insem-2': 20,
                'End Sem': 60
            }
            
            max_marks = max_marks_dict.get(exam, 100)
            
            if marks < 0 or marks > max_marks:
                flash(f'Marks must be between 0 and {max_marks} for {exam}', 'error')
                students = conn.execute('SELECT * FROM students ORDER BY name').fetchall()
                conn.close()
                return render_template('add_marks.html', students=students)
        except ValueError:
            flash('Invalid marks value', 'error')
            students = conn.execute('SELECT * FROM students ORDER BY name').fetchall()
            conn.close()
            return render_template('add_marks.html', students=students)
        
        # Handle file upload
        pdf_path = None
        if 'answer_sheet' in request.files:
            file = request.files['answer_sheet']
            if file and file.filename != '':
                if allowed_file(file.filename):
                    # Create secure filename
                    import time
                    filename = secure_filename(file.filename)
                    timestamp = str(int(time.time() * 1000))
                    filename = f"{student_id}_{subject}_{exam}_{timestamp}.pdf"
                    filepath = os.path.join(app.config['ANSWER_SHEETS_FOLDER'], filename)
                    
                    # Save file
                    file.save(filepath)
                    pdf_path = filepath
                else:
                    flash('Only PDF files are allowed', 'error')
                    students = conn.execute('SELECT * FROM students ORDER BY name').fetchall()
                    conn.close()
                    return render_template('add_marks.html', students=students)
        
        try:
            # Insert marks
            conn.execute(
                '''INSERT INTO marks (student_id, subject, exam, marks, faculty_id)
                   VALUES (?, ?, ?, ?, ?)''',
                (student_id, subject, exam, marks, session['user_id'])
            )
            
            # Insert answer sheet if uploaded
            if pdf_path:
                conn.execute(
                    '''INSERT INTO answer_sheets (student_id, subject, exam, pdf_path, uploaded_by)
                       VALUES (?, ?, ?, ?, ?)''',
                    (student_id, subject, exam, pdf_path, session['user_id'])
                )
            
            conn.commit()
            flash('Marks and answer sheet added successfully!', 'success')
            conn.close()
            return redirect(url_for('faculty_dashboard'))
        except Exception as e:
            flash(f'Error adding marks: {str(e)}', 'error')
            conn.close()
            return redirect(url_for('add_marks'))
    
    # GET request - show form
    students = conn.execute('SELECT * FROM students ORDER BY name').fetchall()
    conn.close()
    return render_template('add_marks.html', students=students)

@app.route('/faculty/complaint/<int:complaint_id>', methods=['GET', 'POST'])
@faculty_login_required
def review_complaint(complaint_id):
    conn = get_db_connection()
    
    if request.method == 'POST':
        status = request.form.get('status')
        remark = request.form.get('remark')
        
        conn.execute(
            'UPDATE complaints SET status = ?, faculty_remark = ? WHERE id = ?',
            (status, remark, complaint_id)
        )
        conn.commit()
        flash('Complaint updated successfully!', 'success')
        conn.close()
        return redirect(url_for('faculty_dashboard'))
    
    complaint = conn.execute(
        '''SELECT c.*, s.name as student_name, s.email as student_email
           FROM complaints c
           JOIN students s ON c.student_id = s.id
           WHERE c.id = ?''',
        (complaint_id,)
    ).fetchone()
    conn.close()
    
    if not complaint:
        flash('Complaint not found', 'error')
        return redirect(url_for('faculty_dashboard'))
    
    return render_template('complaint_review.html', complaint=complaint)

@app.route('/view-answer-sheet/<int:sheet_id>')
@student_login_required
def view_answer_sheet(sheet_id):
    conn = get_db_connection()
    answer_sheet = conn.execute(
        'SELECT * FROM answer_sheets WHERE id = ? AND student_id = ?',
        (sheet_id, session['user_id'])
    ).fetchone()
    conn.close()
    
    if not answer_sheet:
        flash('Answer sheet not found or access denied', 'error')
        return redirect(url_for('student_results'))
    
    # Check if file exists
    if not os.path.exists(answer_sheet['pdf_path']):
        flash('Answer sheet file not found', 'error')
        return redirect(url_for('student_results'))
    
    return send_file(answer_sheet['pdf_path'], mimetype='application/pdf')

# ============================================================================
# ADMIN ROUTES
# ============================================================================

@app.route('/admin/register', methods=['GET', 'POST'])
def admin_register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validation
        if not all([name, email, password, confirm_password]):
            flash('All fields are required', 'error')
            return redirect(url_for('admin_register'))
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return redirect(url_for('admin_register'))
        
        if len(password) < 6:
            flash('Password must be at least 6 characters', 'error')
            return redirect(url_for('admin_register'))
        
        conn = get_db_connection()
        try:
            conn.execute(
                'INSERT INTO admin (name, email, password_hash) VALUES (?, ?, ?)',
                (name, email, generate_password_hash(password))
            )
            conn.commit()
            flash('Admin registration successful! Please login.', 'success')
            return redirect(url_for('admin_login'))
        except sqlite3.IntegrityError:
            flash('Email already exists', 'error')
        finally:
            conn.close()
    
    return render_template('admin_register.html')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        conn = get_db_connection()
        admin = conn.execute('SELECT * FROM admin WHERE email = ?', (email,)).fetchone()
        conn.close()
        
        if admin and check_password_hash(admin['password_hash'], password):
            session.permanent = True  # Enable permanent session (1 hour lifetime)
            session['user_id'] = admin['id']
            session['user_type'] = 'admin'
            session['user_name'] = admin['name']
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid credentials', 'error')
    
    return render_template('admin_login.html')

@app.route('/admin/dashboard')
@admin_login_required
def admin_dashboard():
    conn = get_db_connection()
    
    # Define max marks for validation
    exam_max_marks = {
        'Insem-1': 20,
        'Insem-2': 20,
        'End Sem': 60
    }
    
    # Get statistics
    total_students = conn.execute('SELECT COUNT(*) FROM students').fetchone()[0]
    total_faculty = conn.execute('SELECT COUNT(*) FROM faculty').fetchone()[0]
    total_complaints = conn.execute('SELECT COUNT(*) FROM complaints').fetchone()[0]
    pending_complaints = conn.execute(
        "SELECT COUNT(*) FROM complaints WHERE status = 'Pending Review'"
    ).fetchone()[0]
    
    # Get exam-wise statistics
    exams = conn.execute(
        'SELECT DISTINCT exam FROM marks ORDER BY exam'
    ).fetchall()
    
    exam_stats = []
    for exam_row in exams:
        exam = exam_row['exam']
        
        # Count total marks entries for this exam
        marks_count = conn.execute(
            'SELECT COUNT(*) FROM marks WHERE exam = ?',
            (exam,)
        ).fetchone()[0]
        
        # Count expected entries (students × subjects)
        # For simplicity, we'll use unique subjects in marks table
        subjects_count = conn.execute(
            'SELECT COUNT(DISTINCT subject) FROM marks WHERE exam = ?',
            (exam,)
        ).fetchone()[0]
        
        expected_count = total_students * subjects_count if subjects_count > 0 else 0
        completion_percentage = (marks_count / expected_count * 100) if expected_count > 0 else 0
        
        # Check if results are declared
        result_status = conn.execute(
            'SELECT * FROM result_status WHERE exam = ?',
            (exam,)
        ).fetchone()
        
        is_declared = result_status['is_result_declared'] if result_status else 0
        
        # Get max marks for this exam
        max_marks = exam_max_marks.get(exam, 100)
        
        exam_stats.append({
            'exam': exam,
            'marks_count': marks_count,
            'expected_count': expected_count,
            'completion_percentage': round(completion_percentage, 1),
            'is_declared': is_declared,
            'can_publish': completion_percentage >= 100,
            'max_marks': max_marks
        })
    
    # Get AI-powered insights
    ai_insights = AIDashboardAssistant.get_admin_insights(conn)
    
    conn.close()
    
    return render_template('admin_dashboard.html',
                         total_students=total_students,
                         total_faculty=total_faculty,
                         total_complaints=total_complaints,
                         pending_complaints=pending_complaints,
                         exam_stats=exam_stats,
                         ai_insights=ai_insights)

@app.route('/admin/publish-results/<exam>', methods=['POST'])
@admin_login_required
def publish_results(exam):
    conn = get_db_connection()
    
    try:
        # Check if already published
        result_status = conn.execute(
            'SELECT * FROM result_status WHERE exam = ?',
            (exam,)
        ).fetchone()
        
        if result_status and result_status['is_result_declared'] == 1:
            flash(f'Results for {exam} are already published', 'warning')
            conn.close()
            return redirect(url_for('admin_dashboard'))
        
        # Verify all marks are uploaded
        total_students = conn.execute('SELECT COUNT(*) FROM students').fetchone()[0]
        subjects_count = conn.execute(
            'SELECT COUNT(DISTINCT subject) FROM marks WHERE exam = ?',
            (exam,)
        ).fetchone()[0]
        marks_count = conn.execute(
            'SELECT COUNT(*) FROM marks WHERE exam = ?',
            (exam,)
        ).fetchone()[0]
        
        expected_count = total_students * subjects_count
        
        if marks_count < expected_count:
            flash(f'Cannot publish results. Only {marks_count}/{expected_count} marks uploaded', 'error')
            conn.close()
            return redirect(url_for('admin_dashboard'))
        
        # Publish results
        if result_status:
            # Update existing record
            conn.execute(
                '''UPDATE result_status 
                   SET is_result_declared = 1, declared_by = ?, declared_at = CURRENT_TIMESTAMP
                   WHERE exam = ?''',
                (session['user_id'], exam)
            )
        else:
            # Insert new record
            conn.execute(
                '''INSERT INTO result_status (exam, is_result_declared, declared_by, declared_at)
                   VALUES (?, 1, ?, CURRENT_TIMESTAMP)''',
                (exam, session['user_id'])
            )
        
        # Mark all marks as published for this exam
        conn.execute(
            'UPDATE marks SET is_published = 1 WHERE exam = ?',
            (exam,)
        )
        
        conn.commit()
        flash(f'Results for {exam} published successfully!', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Error publishing results: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/unpublish-results/<exam>', methods=['POST'])
@admin_login_required
def unpublish_results(exam):
    conn = get_db_connection()
    
    try:
        # Update result status
        conn.execute(
            'UPDATE result_status SET is_result_declared = 0 WHERE exam = ?',
            (exam,)
        )
        
        # Mark all marks as unpublished for this exam
        conn.execute(
            'UPDATE marks SET is_published = 0 WHERE exam = ?',
            (exam,)
        )
        
        conn.commit()
        flash(f'Results for {exam} unpublished successfully!', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Error unpublishing results: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('admin_dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('index'))

# ============================================================================
# NOTICE & TIMETABLE MANAGEMENT ROUTES
# ============================================================================

@app.route('/admin/upload-notice', methods=['GET', 'POST'])
@admin_login_required
def admin_upload_notice():
    """Admin page to upload notices and timetables"""
    if request.method == 'POST':
        try:
            # Get form data
            title = request.form.get('title')
            description = request.form.get('description')
            notice_type = request.form.get('notice_type')
            target_role = request.form.get('target_role', 'all')
            department = request.form.get('department')
            semester = request.form.get('semester')
            
            # Validate required fields
            if not title or not notice_type:
                flash('Title and notice type are required', 'error')
                return redirect(request.url)
            
            # Get uploaded file
            if 'pdf_file' not in request.files:
                flash('No file uploaded', 'error')
                return redirect(request.url)
            
            file = request.files['pdf_file']
            if file.filename == '':
                flash('No file selected', 'error')
                return redirect(request.url)
            
            # Upload file using FileHandler
            success, result, file_size = FileHandler.save_file(file, notice_type)
            if not success:
                flash(f'File upload failed: {result}', 'error')
                return redirect(request.url)
            
            file_path = result  # result contains file path
            file_name = file.filename
            
            # Get admin ID from session - use user_id as fallback
            admin_id = session.get('admin_id') or session.get('user_id')
            if not admin_id:
                flash('Session error: Admin ID not found', 'error')
                FileHandler.delete_file(file_path)
                return redirect(url_for('admin_login'))
            
            # Create notice
            notice_id = NoticeService.create_notice(
                title=title,
                description=description,
                file_url=file_path,
                file_name=file_name,
                file_size=file_size,
                notice_type=notice_type,
                target_role=target_role,
                department=department if target_role in ['department', 'class'] else None,
                semester=semester if target_role in ['semester', 'class'] else None,
                uploaded_by=admin_id
            )
            
            if notice_id:
                # Send real-time notifications to targeted students
                targeted_students = NoticeService.get_targeted_students(
                    target_role, department, semester
                )
                
                notification_title = f"New {notice_type.title()}: {title}"
                notification_message = description or f"A new {notice_type} has been uploaded"
                
                for student_id in targeted_students:
                    # Create notification in database
                    NotificationService.create_notification(
                        student_id=student_id,
                        title=notification_title,
                        message=notification_message,
                        notification_type=NOTIFICATION_TYPES['NOTICE']
                    )
                    
                    # Send real-time notification via WebSocket
                    WebSocketHandler.broadcast_notification(
                        socketio,
                        student_id=student_id,
                        notification_data={
                            'title': notification_title,
                            'message': notification_message,
                            'type': 'notice',
                            'notice_id': notice_id
                        }
                    )
                
                flash('Notice uploaded successfully!', 'success')
                return redirect(url_for('admin_manage_notices'))
            else:
                flash('Failed to create notice in database', 'error')
                FileHandler.delete_file(file_path)
                
        except Exception as e:
            flash(f'Error uploading notice: {str(e)}', 'error')
            import traceback
            print(traceback.format_exc())  # Log full error to console
    
    return render_template('admin_upload_notice.html')

@app.route('/admin/manage-notices')
@admin_login_required
def admin_manage_notices():
    """Admin page to manage all notices"""
    notices = NoticeService.get_all_notices()
    stats = NoticeService.get_notice_statistics()
    return render_template('admin_manage_notices.html', notices=notices, stats=stats)

@app.route('/admin/delete-notice/<notice_id>', methods=['POST'])
@admin_login_required
def admin_delete_notice(notice_id):
    """Delete a notice"""
    success = NoticeService.delete_notice(notice_id)
    if success:
        flash('Notice deleted successfully', 'success')
    else:
        flash('Failed to delete notice', 'error')
    return redirect(url_for('admin_manage_notices'))

@app.route('/student/notices')
@student_login_required
def student_notices():
    """Student notice board page"""
    student_id = session.get('user_id')  # Use user_id from session
    
    # Get notices for this student
    notices = NoticeService.get_notices_for_student(student_id)
    
    # Get unread count
    unread_count = NoticeService.get_unread_count(student_id)
    
    return render_template('student_notices.html', 
                         notices=notices, 
                         unread_count=unread_count)

@app.route('/student/timetable')
@student_login_required
def student_timetable():
    """Student timetable page"""
    student_id = session.get('user_id')  # Use user_id from session
    
    # Get timetables for this student (filtered by notice_type)
    timetables = NoticeService.get_notices_for_student(
        student_id=student_id,
        notice_type='timetable'
    )
    
    return render_template('student_timetable.html', timetables=timetables)

@app.route('/download-notice/<notice_id>')
@student_login_required
def download_notice(notice_id):
    """Download a notice PDF"""
    student_id = session.get('user_id')  # Use user_id from session
    
    # Get notice
    notice = NoticeService.get_notice_by_id(notice_id)
    if not notice:
        flash('Notice not found', 'error')
        return redirect(url_for('student_notices'))
    
    # Mark as read
    NoticeService.mark_notice_read(notice_id, student_id)
    
    # Normalize file path (convert backslashes to forward slashes)
    file_path = notice['file_url'].replace('\\', '/')
    
    # Check if file exists
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        flash(f'File not found: {file_path}', 'error')
        return redirect(url_for('student_notices'))

@app.route('/view-notice/<notice_id>')
@student_login_required
def view_notice(notice_id):
    """View a notice PDF in browser"""
    student_id = session.get('user_id')
    
    # Get notice
    notice = NoticeService.get_notice_by_id(notice_id)
    if not notice:
        return "Notice not found", 404
    
    # Mark as read
    NoticeService.mark_notice_read(notice_id, student_id)
    
    # Normalize file path (convert backslashes to forward slashes)
    file_path = notice['file_url'].replace('\\', '/')
    
    # Check if file exists
    if os.path.exists(file_path):
        return send_file(file_path, mimetype='application/pdf')
    else:
        return f"File not found: {file_path}", 404
        return redirect(url_for('student_notices'))

@app.route('/api/notice/mark-read/<notice_id>', methods=['POST'])
@student_login_required
def mark_notice_read(notice_id):
    """API endpoint to mark notice as read"""
    student_id = session.get('user_id')  # Use user_id from session
    success = NoticeService.mark_notice_read(notice_id, student_id)
    return jsonify({'success': success})

@app.route('/api/notices/<notice_id>/read', methods=['POST'])
@student_login_required
def mark_notice_read_alt(notice_id):
    """API endpoint to mark notice as read (alternative URL)"""
    student_id = session.get('user_id')
    success = NoticeService.mark_notice_read(notice_id, student_id)
    return jsonify({'success': success})

@app.route('/api/notice/unread-count')
@student_login_required
def get_unread_count():
    """API endpoint to get unread notice count"""
    student_id = session.get('user_id')  # Use user_id from session
    count = NoticeService.get_unread_count(student_id)
    return jsonify({'count': count})

# ============================================================================
# ASSIGNMENT & EARLY SUBMISSION REWARD ROUTES
# ============================================================================

@app.route('/faculty/assignments')
@faculty_login_required
def faculty_assignments():
    """Faculty assignments dashboard"""
    faculty_id = session['user_id']
    assignments = AssignmentService.get_assignments_by_faculty(faculty_id)
    return render_template('faculty_assignments.html', assignments=assignments)

@app.route('/faculty/assignment/create', methods=['GET', 'POST'])
@faculty_login_required
def create_assignment():
    """Create a new assignment"""
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        subject = request.form.get('subject')
        deadline = request.form.get('deadline')
        max_bonus_marks = request.form.get('max_bonus_marks')
        reward_type = request.form.get('reward_type')
        submission_mode = request.form.get('submission_mode', 'offline')
        
        # Validation
        if not all([title, subject, deadline, max_bonus_marks, reward_type]):
            flash('All required fields must be filled', 'error')
            return redirect(url_for('create_assignment'))
        
        try:
            max_bonus_marks = float(max_bonus_marks)
            if max_bonus_marks <= 0:
                flash('Bonus marks must be positive', 'error')
                return redirect(url_for('create_assignment'))
        except ValueError:
            flash('Invalid bonus marks value', 'error')
            return redirect(url_for('create_assignment'))
        
        # Create assignment
        assignment_id = AssignmentService.create_assignment(
            title=title,
            description=description,
            subject=subject,
            deadline=deadline,
            max_bonus_marks=max_bonus_marks,
            reward_type=reward_type,
            created_by=session['user_id'],
            submission_mode=submission_mode
        )
        
        if assignment_id:
            flash('Assignment created successfully!', 'success')
            return redirect(url_for('faculty_assignments'))
        else:
            flash('Failed to create assignment', 'error')
    
    return render_template('create_assignment.html')

@app.route('/faculty/assignment/<assignment_id>')
@faculty_login_required
def view_assignment_submissions(assignment_id):
    """View submissions for an assignment"""
    assignment = AssignmentService.get_assignment_by_id(assignment_id)
    
    if not assignment or assignment['created_by'] != session['user_id']:
        flash('Assignment not found or access denied', 'error')
        return redirect(url_for('faculty_assignments'))
    
    submissions = AssignmentService.get_submissions_for_assignment(assignment_id)
    stats = AssignmentService.get_assignment_statistics(assignment_id)
    
    return render_template('view_assignment_submissions.html',
                         assignment=assignment,
                         submissions=submissions,
                         stats=stats)

@app.route('/faculty/submission/verify/<submission_id>', methods=['POST'])
@faculty_login_required
def verify_submission(submission_id):
    """Verify a submission"""
    action = request.form.get('action')  # 'approve' or 'reject'
    manual_bonus = request.form.get('manual_bonus')
    notes = request.form.get('notes')
    
    approve = action == 'approve'
    
    # Parse manual bonus if provided
    if manual_bonus:
        try:
            manual_bonus = float(manual_bonus)
        except ValueError:
            manual_bonus = None
    else:
        manual_bonus = None
    
    success, message = AssignmentService.verify_submission(
        submission_id=submission_id,
        faculty_id=session['user_id'],
        approve=approve,
        manual_bonus=manual_bonus,
        notes=notes
    )
    
    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')
    
    # Redirect back to assignment view
    return redirect(request.referrer or url_for('faculty_assignments'))

@app.route('/faculty/submissions/bulk-verify', methods=['POST'])
@faculty_login_required
def bulk_verify_submissions():
    """Bulk verify multiple submissions"""
    submission_ids = request.form.getlist('submission_ids[]')
    
    if not submission_ids:
        flash('No submissions selected', 'error')
        return redirect(request.referrer or url_for('faculty_assignments'))
    
    success_count, total = AssignmentService.bulk_verify_submissions(
        submission_ids, session['user_id']
    )
    
    flash(f'Verified {success_count} out of {total} submissions', 'success')
    return redirect(request.referrer or url_for('faculty_assignments'))

@app.route('/student/assignments')
@student_login_required
def student_assignments():
    """Student assignments dashboard"""
    student_id = session['user_id']
    
    # Get active assignments
    active_assignments = AssignmentService.get_active_assignments()
    
    # Get student's submissions
    my_submissions = AssignmentService.get_student_submissions(student_id)
    
    # Create a set of submitted assignment IDs
    submitted_ids = {sub['assignment_id'] for sub in my_submissions}
    
    # Get current time for deadline comparison
    from datetime import datetime
    current_time = datetime.now().isoformat()
    
    return render_template('student_assignments.html',
                         active_assignments=active_assignments,
                         my_submissions=my_submissions,
                         submitted_ids=submitted_ids,
                         current_time=current_time)

@app.route('/student/assignment/<assignment_id>/submit', methods=['GET', 'POST'])
@student_login_required
def submit_assignment(assignment_id):
    """Submit assignment (online or offline based on assignment mode)"""
    assignment = AssignmentService.get_assignment_by_id(assignment_id)
    
    if not assignment:
        flash('Assignment not found', 'error')
        return redirect(url_for('student_assignments'))
    
    if request.method == 'POST':
        file_path = None
        
        # Handle file upload for online submissions
        if assignment['submission_mode'] == 'online':
            if 'assignment_file' in request.files:
                file = request.files['assignment_file']
                if file and file.filename != '':
                    if allowed_file(file.filename):
                        import time
                        filename = secure_filename(file.filename)
                        timestamp = str(int(time.time() * 1000))
                        filename = f"{session['user_id']}_{assignment_id}_{timestamp}.pdf"
                        filepath = os.path.join(app.config['ASSIGNMENTS_FOLDER'], filename)
                        file.save(filepath)
                        file_path = filepath
                    else:
                        flash('Only PDF files are allowed', 'error')
                        return redirect(url_for('submit_assignment', assignment_id=assignment_id))
                else:
                    flash('Please upload a file for online submission', 'error')
                    return redirect(url_for('submit_assignment', assignment_id=assignment_id))
        
        # Submit assignment
        success, message, bonus = AssignmentService.submit_assignment(
            assignment_id=assignment_id,
            student_id=session['user_id'],
            file_path=file_path
        )
        
        if success:
            if assignment['submission_mode'] == 'online':
                flash(f'{message} AI calculated bonus: {bonus} marks. Your submission will be verified by faculty.', 'success')
            else:
                flash(f'{message} Your submission will be verified by faculty after they check your physical assignment.', 'success')
            return redirect(url_for('student_assignments'))
        else:
            flash(message, 'error')
    
    return render_template('submit_assignment.html', assignment=assignment)

@app.route('/student/internal-marks')
@student_login_required
def student_internal_marks():
    """View internal marks breakdown"""
    student_id = session['user_id']
    
    conn = get_db_connection()
    
    # Get total internal marks
    student = conn.execute(
        'SELECT internal_marks FROM students WHERE id = ?',
        (student_id,)
    ).fetchone()
    
    # Get verified submissions with bonus
    submissions = conn.execute('''
        SELECT s.*, a.title, a.subject, a.max_bonus_marks,
               f.name as faculty_name
        FROM submissions s
        JOIN assignments a ON s.assignment_id = a.id
        JOIN faculty f ON a.created_by = f.id
        WHERE s.student_id = ? AND s.is_verified = 1
        ORDER BY s.verified_at DESC
    ''', (student_id,)).fetchall()
    
    # Get marks log
    marks_log = conn.execute('''
        SELECT l.*, a.title as assignment_title, f.name as changed_by_name
        FROM assignment_marks_log l
        JOIN submissions s ON l.submission_id = s.id
        JOIN assignments a ON s.assignment_id = a.id
        JOIN faculty f ON l.changed_by = f.id
        WHERE l.student_id = ?
        ORDER BY l.changed_at DESC
    ''', (student_id,)).fetchall()
    
    conn.close()
    
    total_internal_marks = student['internal_marks'] if student else 0
    
    return render_template('student_internal_marks.html',
                         total_internal_marks=total_internal_marks,
                         submissions=submissions,
                         marks_log=marks_log)

@app.route('/faculty/assignment/<assignment_id>/deactivate', methods=['POST'])
@faculty_login_required
def deactivate_assignment(assignment_id):
    """Deactivate an assignment"""
    assignment = AssignmentService.get_assignment_by_id(assignment_id)
    
    if not assignment or assignment['created_by'] != session['user_id']:
        flash('Assignment not found or access denied', 'error')
        return redirect(url_for('faculty_assignments'))
    
    if AssignmentService.deactivate_assignment(assignment_id):
        flash('Assignment deactivated successfully', 'success')
    else:
        flash('Failed to deactivate assignment', 'error')
    
    return redirect(url_for('faculty_assignments'))

@app.route('/download-submission/<submission_id>')
@faculty_login_required
def download_submission(submission_id):
    """Download a submission file"""
    conn = get_db_connection()
    submission = conn.execute(
        'SELECT * FROM submissions WHERE id = ?',
        (submission_id,)
    ).fetchone()
    conn.close()
    
    if not submission or not submission['file_path']:
        flash('Submission file not found', 'error')
        return redirect(request.referrer or url_for('faculty_assignments'))
    
    if os.path.exists(submission['file_path']):
        return send_file(submission['file_path'], as_attachment=True)
    else:
        flash('File not found on server', 'error')
        return redirect(request.referrer or url_for('faculty_assignments'))

# ============================================================================
# EXAM & EVENT CALENDAR ROUTES
# ============================================================================

@app.route('/admin/events')
@admin_login_required
def admin_events():
    """Admin events dashboard"""
    admin_id = session['user_id']
    events = EventService.get_events_by_admin(admin_id)
    stats = EventService.get_event_statistics()
    return render_template('admin_events.html', events=events, stats=stats)

@app.route('/admin/event/create', methods=['GET', 'POST'])
@admin_login_required
def create_event():
    """Create a new exam/event"""
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        event_date = request.form.get('event_date')
        start_time = request.form.get('start_time')
        end_time = request.form.get('end_time')
        event_type = request.form.get('event_type')
        target_audience = request.form.get('target_audience')
        semester = request.form.get('semester')
        department = request.form.get('department')
        
        # Validation
        if not all([title, event_date, start_time, end_time, event_type, target_audience]):
            flash('All required fields must be filled', 'error')
            return redirect(url_for('create_event'))
        
        # Validate target audience requirements
        if target_audience in ['semester', 'class'] and not semester:
            flash('Semester is required for semester/class targeting', 'error')
            return redirect(url_for('create_event'))
        
        if target_audience in ['department', 'class'] and not department:
            flash('Department is required for department/class targeting', 'error')
            return redirect(url_for('create_event'))
        
        # Create event
        event_id = EventService.create_event(
            title=title,
            description=description,
            event_date=event_date,
            start_time=start_time,
            end_time=end_time,
            event_type=event_type,
            semester=semester,
            department=department,
            target_audience=target_audience,
            created_by=session['user_id']
        )
        
        if event_id:
            flash('Event created successfully! Email notifications have been sent.', 'success')
            return redirect(url_for('admin_events'))
        else:
            flash('Failed to create event', 'error')
    
    return render_template('create_event.html')

@app.route('/admin/event/<event_id>')
@admin_login_required
def view_event(event_id):
    """View event details"""
    event = EventService.get_event_by_id(event_id)
    
    if not event:
        flash('Event not found', 'error')
        return redirect(url_for('admin_events'))
    
    return render_template('view_event.html', event=event)

@app.route('/admin/event/<event_id>/edit', methods=['GET', 'POST'])
@admin_login_required
def edit_event(event_id):
    """Edit an existing event"""
    event = EventService.get_event_by_id(event_id)
    
    if not event:
        flash('Event not found', 'error')
        return redirect(url_for('admin_events'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        event_date = request.form.get('event_date')
        start_time = request.form.get('start_time')
        end_time = request.form.get('end_time')
        event_type = request.form.get('event_type')
        target_audience = request.form.get('target_audience')
        semester = request.form.get('semester')
        department = request.form.get('department')
        
        # Update event
        success = EventService.update_event(
            event_id=event_id,
            title=title,
            description=description,
            event_date=event_date,
            start_time=start_time,
            end_time=end_time,
            event_type=event_type,
            semester=semester,
            department=department,
            target_audience=target_audience
        )
        
        if success:
            flash('Event updated successfully! Update notifications have been sent.', 'success')
            return redirect(url_for('admin_events'))
        else:
            flash('Failed to update event', 'error')
    
    return render_template('edit_event.html', event=event)

@app.route('/admin/event/<event_id>/delete', methods=['POST'])
@admin_login_required
def delete_event(event_id):
    """Delete an event"""
    success = EventService.delete_event(event_id)
    
    if success:
        flash('Event cancelled successfully! Cancellation notifications have been sent.', 'success')
    else:
        flash('Failed to cancel event', 'error')
    
    return redirect(url_for('admin_events'))

@app.route('/student/calendar')
@student_login_required
def student_calendar():
    """Student calendar dashboard"""
    student_id = session['user_id']
    upcoming_events = EventService.get_upcoming_events(student_id, days_ahead=30)
    return render_template('student_calendar.html', upcoming_events=upcoming_events)

@app.route('/api/calendar/events')
@student_login_required
def api_calendar_events():
    """API endpoint for calendar events"""
    student_id = session['user_id']
    start_date = request.args.get('start')
    end_date = request.args.get('end')
    
    events = EventService.get_calendar_events(
        student_id=student_id,
        start_date=start_date,
        end_date=end_date
    )
    
    return jsonify(events)

@app.route('/api/event/<event_id>')
@student_login_required
def api_event_details(event_id):
    """API endpoint for event details"""
    event = EventService.get_event_by_id(event_id)
    
    if not event:
        return jsonify({'error': 'Event not found'}), 404
    
    # Convert to JSON-serializable format
    event_data = {
        'id': event['id'],
        'title': event['title'],
        'description': event['description'],
        'event_date': event['event_date'],
        'start_time': event['start_time'],
        'end_time': event['end_time'],
        'event_type': event['event_type'],
        'semester': event['semester'],
        'department': event['department'],
        'created_by_name': event['created_by_name']
    }
    
    return jsonify(event_data)

if __name__ == '__main__':
    # For production: Set debug=False to prevent session invalidation on code changes
    # For development: Use debug=True but be aware sessions may reset on file changes
    socketio.run(app, debug=True, port=5000, allow_unsafe_werkzeug=True)
