"""
Enhanced Flask Application with Real-time Notifications
Integrates WebSocket support for instant notification delivery
"""

from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file, jsonify
from flask_socketio import SocketIO
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
from datetime import timedelta
import sqlite3
import os
import logging

# Import existing utilities
from utils.ai_processor import analyze_complaint
from utils.pdf_highlighter import highlight_pdf
from models.database_models import init_db, get_db_connection

# Import notification services
from utils.notification_service import NotificationService, NOTIFICATION_TYPES
from utils.websocket_handler import WebSocketHandler

# Import notice services
from utils.notice_service import NoticeService, NOTICE_TYPES
from utils.file_handler import FileHandler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# CRITICAL: Fixed SECRET_KEY
app.config['SECRET_KEY'] = 'academic_grievance_system_fixed_secret_key_2024_do_not_change'

# Session Configuration
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_REFRESH_EACH_REQUEST'] = True

# Upload Configuration
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ANSWER_SHEETS_FOLDER'] = 'static/uploads/answer_sheets'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
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

@socketio.on('mark_read')
def handle_mark_read(data):
    """Handle mark notification as read"""
    WebSocketHandler.handle_mark_read(data)

@socketio.on('mark_all_read')
def handle_mark_all_read():
    """Handle mark all notifications as read"""
    WebSocketHandler.handle_mark_all_read()

@socketio.on('get_unread_count')
def handle_get_unread_count():
    """Handle get unread count request"""
    WebSocketHandler.handle_get_unread_count()

# ============================================================================
# NOTIFICATION API ENDPOINTS
# ============================================================================

@app.route('/api/notifications')
def get_notifications():
    """Get all notifications for current student"""
    if session.get('user_type') != 'student':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    student_id = session.get('user_id')
    notifications = NotificationService.get_all_notifications(student_id, limit=50)
    unread_count = NotificationService.get_unread_count(student_id)
    
    return jsonify({
        'success': True,
        'notifications': notifications,
        'unread_count': unread_count
    })

@app.route('/api/notifications/<int:notification_id>/read', methods=['POST'])
def mark_notification_read(notification_id):
    """Mark a notification as read"""
    if session.get('user_type') != 'student':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    student_id = session.get('user_id')
    success = NotificationService.mark_as_read(notification_id, student_id)
    
    return jsonify({'success': success})

@app.route('/api/notifications/mark-all-read', methods=['POST'])
def mark_all_notifications_read():
    """Mark all notifications as read"""
    if session.get('user_type') != 'student':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    student_id = session.get('user_id')
    success = NotificationService.mark_all_as_read(student_id)
    
    return jsonify({'success': success})

@app.route('/api/notifications/<int:notification_id>', methods=['DELETE'])
def delete_notification(notification_id):
    """Delete a notification"""
    if session.get('user_type') != 'student':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    student_id = session.get('user_id')
    success = NotificationService.delete_notification(notification_id, student_id)
    
    return jsonify({'success': success})

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def send_notification(student_id, title, message, notification_type, related_id=None):
    """
    Helper function to create and broadcast notification
    
    Args:
        student_id: ID of student to notify
        title: Notification title
        message: Notification message
        notification_type: Type of notification
        related_id: Optional related entity ID
    """
    try:
        # Create notification in database
        notification_id = NotificationService.create_notification(
            student_id, title, message, notification_type, related_id
        )
        
        if notification_id:
            # Prepare notification data for WebSocket
            notification_data = {
                'id': notification_id,
                'title': title,
                'message': message,
                'type': notification_type,
                'related_id': related_id,
                'is_read': 0,
                'created_at': 'Just now'
            }
            
            # Broadcast via WebSocket
            WebSocketHandler.broadcast_notification(socketio, student_id, notification_data)
            
            logger.info(f"Notification sent to student {student_id}: {title}")
            return True
    except Exception as e:
        logger.error(f"Error sending notification: {e}")
    
    return False

# Session refresh handler
@app.before_request
def refresh_session():
    """Refresh session on each request"""
    if 'user_id' in session:
        session.permanent = True
        session.modified = True

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

# ============================================================================
# EXISTING ROUTES (with notification integration)
# ============================================================================

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
            session.permanent = True
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
            session.permanent = True
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
    conn = get_db_connection()
    complaints = conn.execute(
        'SELECT * FROM complaints WHERE student_id = ? ORDER BY id DESC',
        (session['user_id'],)
    ).fetchall()
    conn.close()
    
    # Get unread notice count
    unread_notice_count = NoticeService.get_unread_count(session['user_id'])
    
    return render_template('student_dashboard.html', 
                         complaints=complaints,
                         unread_notice_count=unread_notice_count)

# Continue with remaining routes in next part...

@app.route('/student/results')
@student_login_required
def student_results():
    conn = get_db_connection()
    
    exam_max_marks = {
        'Insem-1': 20,
        'Insem-2': 20,
        'End Sem': 60
    }
    
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
    
    for exam_data in exams_dict.values():
        max_marks_per_subject = exam_data['max_marks_per_subject']
        total_percentage = 0
        for result in exam_data['results']:
            subject_percentage = (result['marks'] / max_marks_per_subject) * 100
            total_percentage += subject_percentage
        
        num_subjects = len(exam_data['results'])
        average_percentage = total_percentage / num_subjects if num_subjects > 0 else 0
        total_marks = sum(r['marks'] for r in exam_data['results'])
        total_possible = num_subjects * max_marks_per_subject
        
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
        
        answer_sheet = conn.execute(
            'SELECT * FROM answer_sheets WHERE student_id = ? AND subject = ? AND exam = ?',
            (session['user_id'], subject, exam)
        ).fetchone()
        
        if not answer_sheet:
            flash('No answer sheet found for this subject and exam', 'error')
            conn.close()
            return redirect(url_for('new_complaint'))
        
        ai_result = analyze_complaint(complaint_text)
        
        highlighted_path = None
        if answer_sheet['pdf_path'] and ai_result['question_number']:
            highlighted_path = highlight_pdf(
                answer_sheet['pdf_path'],
                ai_result['question_number']
            )
        
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
    complaints = conn.execute(
        '''SELECT c.*, s.name as student_name, s.email as student_email
           FROM complaints c
           JOIN students s ON c.student_id = s.id
           ORDER BY c.id DESC'''
    ).fetchall()
    conn.close()
    
    return render_template('faculty_dashboard.html', complaints=complaints)

@app.route('/faculty/add-marks', methods=['GET', 'POST'])
@faculty_login_required
def add_marks():
    conn = get_db_connection()
    
    if request.method == 'POST':
        student_id = request.form.get('student_id')
        subject = request.form.get('subject')
        exam = request.form.get('exam')
        marks = request.form.get('marks')
        
        if not all([student_id, subject, exam, marks]):
            flash('All fields are required', 'error')
            students = conn.execute('SELECT * FROM students ORDER BY name').fetchall()
            conn.close()
            return render_template('add_marks.html', students=students)
        
        try:
            marks = int(marks)
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
        
        pdf_path = None
        if 'answer_sheet' in request.files:
            file = request.files['answer_sheet']
            if file and file.filename != '':
                if allowed_file(file.filename):
                    import time
                    filename = secure_filename(file.filename)
                    timestamp = str(int(time.time() * 1000))
                    filename = f"{student_id}_{subject}_{exam}_{timestamp}.pdf"
                    filepath = os.path.join(app.config['ANSWER_SHEETS_FOLDER'], filename)
                    file.save(filepath)
                    pdf_path = filepath
                else:
                    flash('Only PDF files are allowed', 'error')
                    students = conn.execute('SELECT * FROM students ORDER BY name').fetchall()
                    conn.close()
                    return render_template('add_marks.html', students=students)
        
        try:
            conn.execute(
                '''INSERT INTO marks (student_id, subject, exam, marks, faculty_id)
                   VALUES (?, ?, ?, ?, ?)''',
                (student_id, subject, exam, marks, session['user_id'])
            )
            
            if pdf_path:
                conn.execute(
                    '''INSERT INTO answer_sheets (student_id, subject, exam, pdf_path, uploaded_by)
                       VALUES (?, ?, ?, ?, ?)''',
                    (student_id, subject, exam, pdf_path, session['user_id'])
                )
                
                # Send notification for PDF upload
                send_notification(
                    int(student_id),
                    f"Answer Sheet Available: {subject}",
                    f"Your answer sheet for {subject} - {exam} is now available for viewing",
                    NOTIFICATION_TYPES['PDF_UPLOAD']
                )
            
            conn.commit()
            
            # Send notification for marks upload
            faculty_name = session.get('user_name', 'Faculty')
            send_notification(
                int(student_id),
                f"New Marks: {subject}",
                f"Your marks for {subject} - {exam} have been uploaded by {faculty_name}. Score: {marks}/{max_marks}",
                NOTIFICATION_TYPES['MARKS']
            )
            
            flash('Marks and answer sheet added successfully!', 'success')
            conn.close()
            return redirect(url_for('faculty_dashboard'))
        except Exception as e:
            flash(f'Error adding marks: {str(e)}', 'error')
            conn.close()
            return redirect(url_for('add_marks'))
    
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
        
        # Get complaint details before update
        complaint = conn.execute(
            'SELECT student_id, subject, exam FROM complaints WHERE id = ?',
            (complaint_id,)
        ).fetchone()
        
        conn.execute(
            'UPDATE complaints SET status = ?, faculty_remark = ? WHERE id = ?',
            (status, remark, complaint_id)
        )
        conn.commit()
        
        # Send notification to student
        if complaint:
            send_notification(
                complaint['student_id'],
                f"Grievance Update: {complaint['subject']}",
                f"Your grievance for {complaint['subject']} - {complaint['exam']} has been {status.lower()}. {remark if remark else ''}",
                NOTIFICATION_TYPES['GRIEVANCE'],
                complaint_id
            )
        
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
    
    if not os.path.exists(answer_sheet['pdf_path']):
        flash('Answer sheet file not found', 'error')
        return redirect(url_for('student_results'))
    
    return send_file(answer_sheet['pdf_path'], mimetype='application/pdf')

# ============================================================================
# ADMIN ROUTES (with notification integration)
# ============================================================================

@app.route('/admin/register', methods=['GET', 'POST'])
def admin_register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
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
            session.permanent = True
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
    
    exam_max_marks = {
        'Insem-1': 20,
        'Insem-2': 20,
        'End Sem': 60
    }
    
    total_students = conn.execute('SELECT COUNT(*) FROM students').fetchone()[0]
    total_faculty = conn.execute('SELECT COUNT(*) FROM faculty').fetchone()[0]
    total_complaints = conn.execute('SELECT COUNT(*) FROM complaints').fetchone()[0]
    pending_complaints = conn.execute(
        "SELECT COUNT(*) FROM complaints WHERE status = 'Pending Review'"
    ).fetchone()[0]
    
    # Get notification statistics
    notification_stats = NotificationService.get_notification_stats()
    
    # Get notice statistics
    notice_stats = NoticeService.get_notice_statistics()
    
    exams = conn.execute(
        'SELECT DISTINCT exam FROM marks ORDER BY exam'
    ).fetchall()
    
    exam_stats = []
    for exam_row in exams:
        exam = exam_row['exam']
        
        marks_count = conn.execute(
            'SELECT COUNT(*) FROM marks WHERE exam = ?',
            (exam,)
        ).fetchone()[0]
        
        subjects_count = conn.execute(
            'SELECT COUNT(DISTINCT subject) FROM marks WHERE exam = ?',
            (exam,)
        ).fetchone()[0]
        
        expected_count = total_students * subjects_count if subjects_count > 0 else 0
        completion_percentage = (marks_count / expected_count * 100) if expected_count > 0 else 0
        
        result_status = conn.execute(
            'SELECT * FROM result_status WHERE exam = ?',
            (exam,)
        ).fetchone()
        
        is_declared = result_status['is_result_declared'] if result_status else 0
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
    
    conn.close()
    
    return render_template('admin_dashboard.html',
                         total_students=total_students,
                         total_faculty=total_faculty,
                         total_complaints=total_complaints,
                         pending_complaints=pending_complaints,
                         exam_stats=exam_stats,
                         notification_stats=notification_stats,
                         notice_stats=notice_stats)

@app.route('/admin/publish-results/<exam>', methods=['POST'])
@admin_login_required
def publish_results(exam):
    conn = get_db_connection()
    
    try:
        result_status = conn.execute(
            'SELECT * FROM result_status WHERE exam = ?',
            (exam,)
        ).fetchone()
        
        if result_status and result_status['is_result_declared'] == 1:
            flash(f'Results for {exam} are already published', 'warning')
            conn.close()
            return redirect(url_for('admin_dashboard'))
        
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
        
        if result_status:
            conn.execute(
                '''UPDATE result_status 
                   SET is_result_declared = 1, declared_by = ?, declared_at = CURRENT_TIMESTAMP
                   WHERE exam = ?''',
                (session['user_id'], exam)
            )
        else:
            conn.execute(
                '''INSERT INTO result_status (exam, is_result_declared, declared_by, declared_at)
                   VALUES (?, 1, ?, CURRENT_TIMESTAMP)''',
                (exam, session['user_id'])
            )
        
        conn.execute(
            'UPDATE marks SET is_published = 1 WHERE exam = ?',
            (exam,)
        )
        
        conn.commit()
        
        # Send notifications to all students who have marks for this exam
        students = conn.execute(
            'SELECT DISTINCT student_id FROM marks WHERE exam = ?',
            (exam,)
        ).fetchall()
        
        for student in students:
            send_notification(
                student['student_id'],
                f"Results Published: {exam}",
                f"The results for {exam} have been officially published. Check your results now!",
                NOTIFICATION_TYPES['RESULT']
            )
        
        flash(f'Results for {exam} published successfully! Notifications sent to {len(students)} students.', 'success')
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
        conn.execute(
            'UPDATE result_status SET is_result_declared = 0 WHERE exam = ?',
            (exam,)
        )
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
            title = request.form.get('title')
            description = request.form.get('description', '')
            notice_type = request.form.get('notice_type')
            target_role = request.form.get('target_role', 'all')
            department = request.form.get('department')
            semester = request.form.get('semester')
            publish_at = request.form.get('publish_at')
            
            if not all([title, notice_type]):
                flash('Title and notice type are required', 'error')
                return redirect(url_for('admin_upload_notice'))
            
            if 'pdf_file' not in request.files:
                flash('No file uploaded', 'error')
                return redirect(url_for('admin_upload_notice'))
            
            file = request.files['pdf_file']
            success, result, file_size = FileHandler.save_file(file, notice_type)
            
            if not success:
                flash(f'File upload failed: {result}', 'error')
                return redirect(url_for('admin_upload_notice'))
            
            file_path = result
            file_name = file.filename
            
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
                uploaded_by=session['user_id'],
                publish_at=publish_at if publish_at else None
            )
            
            if not notice_id:
                flash('Error creating notice in database', 'error')
                FileHandler.delete_file(file_path)
                return redirect(url_for('admin_upload_notice'))
            
            targeted_students = NoticeService.get_targeted_students(
                target_role, department, semester
            )
            
            notification_title = f"New {notice_type.title()}: {title}"
            notification_message = f"A new {notice_type} has been uploaded. Click to view."
            
            for student_id in targeted_students:
                notif_id = NotificationService.create_notification(
                    student_id=student_id,
                    title=notification_title,
                    message=notification_message,
                    notification_type=NOTIFICATION_TYPES['NOTICE'],
                    related_id=notice_id
                )
                
                if notif_id:
                    notification_data = {
                        'id': notif_id,
                        'title': notification_title,
                        'message': notification_message,
                        'type': 'notice',
                        'related_id': notice_id,
                        'is_read': 0,
                        'created_at': 'Just now'
                    }
                    WebSocketHandler.broadcast_notification(socketio, student_id, notification_data)
            
            flash(f'Notice uploaded successfully! Notifications sent to {len(targeted_students)} students.', 'success')
            return redirect(url_for('admin_manage_notices'))
            
        except Exception as e:
            logger.error(f"Error uploading notice: {e}")
            flash(f'Error uploading notice: {str(e)}', 'error')
            return redirect(url_for('admin_upload_notice'))
    
    return render_template('admin_upload_notice.html')

@app.route('/admin/manage-notices')
@admin_login_required
def admin_manage_notices():
    """Admin page to manage all notices"""
    notice_type = request.args.get('type')
    notices = NoticeService.get_all_notices(notice_type=notice_type)
    return render_template('admin_manage_notices.html', notices=notices)

@app.route('/admin/notice/<int:notice_id>/delete', methods=['POST'])
@admin_login_required
def admin_delete_notice(notice_id):
    """Delete a notice"""
    success = NoticeService.delete_notice(notice_id)
    if success:
        flash('Notice deleted successfully!', 'success')
    else:
        flash('Error deleting notice', 'error')
    return redirect(url_for('admin_manage_notices'))

@app.route('/student/notices')
@student_login_required
def student_notices():
    """Student page to view all notices"""
    notices = NoticeService.get_notices_for_student(
        student_id=session['user_id'],
        notice_type=None
    )
    unread_count = NoticeService.get_unread_count(session['user_id'])
    return render_template('student_notices.html', 
                         notices=notices, 
                         unread_count=unread_count)

@app.route('/student/timetable')
@student_login_required
def student_timetable():
    """Student page to view timetable"""
    timetables = NoticeService.get_notices_for_student(
        student_id=session['user_id'],
        notice_type=NOTICE_TYPES['TIMETABLE'],
        limit=10
    )
    current_timetable = timetables[0] if timetables else None
    previous_timetables = timetables[1:] if len(timetables) > 1 else []
    return render_template('student_timetable.html',
                         timetable=current_timetable,
                         previous_timetables=previous_timetables)

@app.route('/download-notice/<int:notice_id>')
@student_login_required
def download_notice(notice_id):
    """Download a notice PDF"""
    notice = NoticeService.get_notice_by_id(notice_id)
    if not notice:
        flash('Notice not found', 'error')
        return redirect(url_for('student_notices'))
    
    student_id = session['user_id']
    notices = NoticeService.get_notices_for_student(student_id)
    notice_ids = [n['id'] for n in notices]
    
    if notice_id not in notice_ids:
        flash('Access denied', 'error')
        return redirect(url_for('student_notices'))
    
    NoticeService.increment_download_count(notice_id)
    NoticeService.mark_notice_read(notice_id, student_id)
    
    file_path = notice['file_url']
    if os.path.exists(file_path):
        return send_file(file_path, 
                        as_attachment=True,
                        download_name=notice['file_name'])
    else:
        flash('File not found', 'error')
        return redirect(url_for('student_notices'))

@app.route('/api/notices/<int:notice_id>/read', methods=['POST'])
@student_login_required
def api_mark_notice_read(notice_id):
    """Mark a notice as read"""
    success = NoticeService.mark_notice_read(notice_id, session['user_id'])
    return jsonify({'success': success})

@app.route('/api/notices/unread-count')
@student_login_required
def api_notice_unread_count():
    """Get unread notice count"""
    count = NoticeService.get_unread_count(session['user_id'])
    return jsonify({'count': count})

@app.route('/api/notices/stats')
@admin_login_required
def api_notice_stats():
    """Get notice statistics for admin"""
    stats = NoticeService.get_notice_statistics()
    return jsonify(stats)

# ============================================================================
# RUN APPLICATION
# ============================================================================

if __name__ == '__main__':
    # Use socketio.run instead of app.run for WebSocket support
    socketio.run(
        app,
        debug=True,
        host='0.0.0.0',
        port=5000,
        use_reloader=True
    )
