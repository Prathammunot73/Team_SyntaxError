import sqlite3
from werkzeug.security import generate_password_hash

DATABASE = 'database.db'

def get_db_connection():
    """Create and return a database connection"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database with tables and sample data"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create students table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create faculty table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS faculty (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            subject TEXT NOT NULL,
            department TEXT,
            employee_id TEXT UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create answer_sheets table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS answer_sheets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            subject TEXT NOT NULL,
            exam TEXT NOT NULL,
            pdf_path TEXT NOT NULL,
            uploaded_by INTEGER,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students (id),
            FOREIGN KEY (uploaded_by) REFERENCES faculty (id)
        )
    ''')
    
    # Create marks table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS marks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            subject TEXT NOT NULL,
            exam TEXT NOT NULL,
            marks INTEGER NOT NULL,
            faculty_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students (id),
            FOREIGN KEY (faculty_id) REFERENCES faculty (id)
        )
    ''')
    
    # Create complaints table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            subject TEXT NOT NULL,
            exam TEXT NOT NULL,
            complaint_text TEXT NOT NULL,
            extracted_question TEXT,
            ai_summary TEXT,
            highlighted_pdf_path TEXT,
            status TEXT DEFAULT 'Pending Review',
            faculty_remark TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students (id)
        )
    ''')
    
    # Create admin table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admin (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create result_status table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS result_status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            exam TEXT UNIQUE NOT NULL,
            is_result_declared INTEGER DEFAULT 0,
            declared_by INTEGER,
            declared_at TIMESTAMP,
            FOREIGN KEY (declared_by) REFERENCES admin (id)
        )
    ''')
    
    # Create marks published flag
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS marks_temp AS SELECT * FROM marks WHERE 1=0
    ''')
    cursor.execute('DROP TABLE IF EXISTS marks_temp')
    
    # Add is_published column to marks if it doesn't exist
    try:
        cursor.execute('ALTER TABLE marks ADD COLUMN is_published INTEGER DEFAULT 0')
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    # Create notifications table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            type TEXT NOT NULL,
            related_id INTEGER,
            is_read INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students (id)
        )
    ''')
    
    # Create index for faster queries
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_notifications_student 
        ON notifications(student_id, is_read, created_at DESC)
    ''')
    
    # Add department and semester columns to students if they don't exist
    try:
        cursor.execute('ALTER TABLE students ADD COLUMN department TEXT')
    except sqlite3.OperationalError:
        pass
    
    try:
        cursor.execute('ALTER TABLE students ADD COLUMN semester TEXT')
    except sqlite3.OperationalError:
        pass
    
    # Create notices table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            file_url TEXT NOT NULL,
            file_name TEXT NOT NULL,
            file_size INTEGER,
            notice_type TEXT NOT NULL,
            target_role TEXT DEFAULT 'all',
            department TEXT,
            semester TEXT,
            uploaded_by INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            publish_at TIMESTAMP,
            is_published INTEGER DEFAULT 1,
            download_count INTEGER DEFAULT 0,
            FOREIGN KEY (uploaded_by) REFERENCES admin (id)
        )
    ''')
    
    # Create notice_reads table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notice_reads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            notice_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            is_read INTEGER DEFAULT 0,
            read_at TIMESTAMP,
            FOREIGN KEY (notice_id) REFERENCES notices (id),
            FOREIGN KEY (student_id) REFERENCES students (id),
            UNIQUE(notice_id, student_id)
        )
    ''')
    
    # Create indexes for notices
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_notices_type 
        ON notices(notice_type, created_at DESC)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_notices_target 
        ON notices(target_role, department, semester)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_notice_reads 
        ON notice_reads(student_id, is_read)
    ''')
    
    # Create assignments table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS assignments (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT,
            subject TEXT NOT NULL,
            deadline TIMESTAMP NOT NULL,
            max_bonus_marks REAL NOT NULL,
            reward_type TEXT NOT NULL,
            submission_mode TEXT DEFAULT 'offline',
            created_by INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active INTEGER DEFAULT 1,
            FOREIGN KEY (created_by) REFERENCES faculty (id)
        )
    ''')
    
    # Create submissions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS submissions (
            id TEXT PRIMARY KEY,
            assignment_id TEXT NOT NULL,
            student_id INTEGER NOT NULL,
            submission_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            file_path TEXT,
            is_verified INTEGER DEFAULT 0,
            ai_bonus_marks REAL DEFAULT 0,
            teacher_final_bonus REAL,
            teacher_notes TEXT,
            verified_by INTEGER,
            verified_at TIMESTAMP,
            FOREIGN KEY (assignment_id) REFERENCES assignments (id),
            FOREIGN KEY (student_id) REFERENCES students (id),
            FOREIGN KEY (verified_by) REFERENCES faculty (id),
            UNIQUE(assignment_id, student_id)
        )
    ''')
    
    # Create assignment_marks_log table for audit trail
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS assignment_marks_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            submission_id TEXT NOT NULL,
            student_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            old_value REAL,
            new_value REAL,
            changed_by INTEGER NOT NULL,
            changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            notes TEXT,
            FOREIGN KEY (submission_id) REFERENCES submissions (id),
            FOREIGN KEY (student_id) REFERENCES students (id),
            FOREIGN KEY (changed_by) REFERENCES faculty (id)
        )
    ''')
    
    # Create indexes for assignments
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_assignments_faculty 
        ON assignments(created_by, created_at DESC)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_assignments_active 
        ON assignments(is_active, deadline)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_submissions_assignment 
        ON submissions(assignment_id, submission_time)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_submissions_student 
        ON submissions(student_id, submission_time DESC)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_submissions_verified 
        ON submissions(is_verified, assignment_id)
    ''')
    
    # Add internal_marks column to students if it doesn't exist
    try:
        cursor.execute('ALTER TABLE students ADD COLUMN internal_marks REAL DEFAULT 0')
    except sqlite3.OperationalError:
        pass
    
    # Create exam_events table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS exam_events (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT,
            event_date DATE NOT NULL,
            start_time TIME NOT NULL,
            end_time TIME NOT NULL,
            event_type TEXT NOT NULL,
            semester TEXT,
            department TEXT,
            target_audience TEXT DEFAULT 'all',
            created_by INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active INTEGER DEFAULT 1,
            FOREIGN KEY (created_by) REFERENCES admin (id)
        )
    ''')
    
    # Create event_notifications table for tracking sent emails
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS event_notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id TEXT NOT NULL,
            student_id INTEGER NOT NULL,
            notification_type TEXT NOT NULL,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            email_status TEXT DEFAULT 'sent',
            FOREIGN KEY (event_id) REFERENCES exam_events (id),
            FOREIGN KEY (student_id) REFERENCES students (id),
            UNIQUE(event_id, student_id, notification_type)
        )
    ''')
    
    # Create indexes for exam_events
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_exam_events_date 
        ON exam_events(event_date, is_active)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_exam_events_target 
        ON exam_events(target_audience, semester, department)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_event_notifications 
        ON event_notifications(event_id, student_id)
    ''')
    
    conn.commit()
    
    # Insert sample data if tables are empty
    student_count = cursor.execute('SELECT COUNT(*) FROM students').fetchone()[0]
    
    if student_count == 0:
        # Sample students
        cursor.execute(
            'INSERT INTO students (name, email, password_hash) VALUES (?, ?, ?)',
            ('John Doe', 'john@student.com', generate_password_hash('student123'))
        )
        cursor.execute(
            'INSERT INTO students (name, email, password_hash) VALUES (?, ?, ?)',
            ('Jane Smith', 'jane@student.com', generate_password_hash('student123'))
        )
        
        # Sample faculty
        cursor.execute(
            'INSERT INTO faculty (name, email, subject, department, employee_id, password_hash) VALUES (?, ?, ?, ?, ?, ?)',
            ('Dr. Robert Brown', 'robert@faculty.com', 'Mathematics', 'Science', 'EMP001', generate_password_hash('faculty123'))
        )
        cursor.execute(
            'INSERT INTO faculty (name, email, subject, department, employee_id, password_hash) VALUES (?, ?, ?, ?, ?, ?)',
            ('Prof. Sarah Wilson', 'sarah@faculty.com', 'Physics', 'Science', 'EMP002', generate_password_hash('faculty123'))
        )
        
        # Sample answer sheets
        cursor.execute(
            '''INSERT INTO answer_sheets (student_id, subject, exam, pdf_path, uploaded_by) 
               VALUES (?, ?, ?, ?, ?)''',
            (1, 'Mathematics', 'Mid-Term 2024', 'static/uploads/sample_answer_sheet.pdf', 1)
        )
        cursor.execute(
            '''INSERT INTO answer_sheets (student_id, subject, exam, pdf_path, uploaded_by) 
               VALUES (?, ?, ?, ?, ?)''',
            (1, 'Physics', 'Final 2024', 'static/uploads/sample_physics_sheet.pdf', 2)
        )
        
        # Sample marks
        cursor.execute(
            '''INSERT INTO marks (student_id, subject, exam, marks, faculty_id) 
               VALUES (?, ?, ?, ?, ?)''',
            (1, 'Mathematics', 'Mid-Term 2024', 75, 1)
        )
        cursor.execute(
            '''INSERT INTO marks (student_id, subject, exam, marks, faculty_id) 
               VALUES (?, ?, ?, ?, ?)''',
            (1, 'Physics', 'Final 2024', 82, 2)
        )
        cursor.execute(
            '''INSERT INTO marks (student_id, subject, exam, marks, faculty_id) 
               VALUES (?, ?, ?, ?, ?)''',
            (2, 'Mathematics', 'Mid-Term 2024', 88, 1)
        )
        
        conn.commit()
        print("✓ Database initialized with sample data")
        print("  Student Login: john@student.com / student123")
        print("  Faculty Login: robert@faculty.com / faculty123")
    
    conn.close()
