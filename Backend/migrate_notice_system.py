"""
Migration Script: Add Notice & Timetable Management System
Run this script to add notice/timetable tables and features
"""

import sqlite3
import os
from datetime import datetime
import shutil

DATABASE = 'database.db'

def backup_database():
    """Create a backup of the current database"""
    if os.path.exists(DATABASE):
        backup_name = f'database_backup_notices_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
        shutil.copy2(DATABASE, backup_name)
        print(f"✓ Database backed up to: {backup_name}")
        return backup_name
    return None

def check_table_exists(cursor, table_name):
    """Check if a table exists in the database"""
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,)
    )
    return cursor.fetchone() is not None

def add_student_columns(conn):
    """Add department and semester columns to students table"""
    cursor = conn.cursor()
    
    # Check if columns exist
    cursor.execute("PRAGMA table_info(students)")
    columns = [column[1] for column in cursor.fetchall()]
    
    changes_made = False
    
    if 'department' not in columns:
        print("Adding department column to students table...")
        cursor.execute('ALTER TABLE students ADD COLUMN department TEXT')
        changes_made = True
    else:
        print("⚠ department column already exists in students table")
    
    if 'semester' not in columns:
        print("Adding semester column to students table...")
        cursor.execute('ALTER TABLE students ADD COLUMN semester TEXT')
        changes_made = True
    else:
        print("⚠ semester column already exists in students table")
    
    if changes_made:
        conn.commit()
        print("✓ Student columns added successfully")
    
    return changes_made

def create_notices_table(conn):
    """Create notices table"""
    cursor = conn.cursor()
    
    if check_table_exists(cursor, 'notices'):
        print("⚠ Notices table already exists, skipping...")
        return False
    
    print("Creating notices table...")
    cursor.execute('''
        CREATE TABLE notices (
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
    
    conn.commit()
    print("✓ Notices table created successfully")
    return True

def create_notice_reads_table(conn):
    """Create notice_reads table"""
    cursor = conn.cursor()
    
    if check_table_exists(cursor, 'notice_reads'):
        print("⚠ Notice_reads table already exists, skipping...")
        return False
    
    print("Creating notice_reads table...")
    cursor.execute('''
        CREATE TABLE notice_reads (
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
    
    conn.commit()
    print("✓ Notice_reads table created successfully")
    return True

def create_indexes(conn):
    """Create indexes for better performance"""
    cursor = conn.cursor()
    
    print("Creating indexes...")
    
    indexes = [
        ('idx_notices_type', 'CREATE INDEX IF NOT EXISTS idx_notices_type ON notices(notice_type, created_at DESC)'),
        ('idx_notices_target', 'CREATE INDEX IF NOT EXISTS idx_notices_target ON notices(target_role, department, semester)'),
        ('idx_notice_reads', 'CREATE INDEX IF NOT EXISTS idx_notice_reads ON notice_reads(student_id, is_read)')
    ]
    
    for idx_name, idx_sql in indexes:
        cursor.execute(idx_sql)
        print(f"  ✓ Created index: {idx_name}")
    
    conn.commit()
    print("✓ All indexes created successfully")

def create_upload_folders():
    """Create upload folders for notices"""
    folders = [
        'static/uploads/notices',
        'static/uploads/notices/timetables',
        'static/uploads/notices/general',
        'static/uploads/notices/exams',
        'static/uploads/notices/events'
    ]
    
    print("\nCreating upload folders...")
    for folder in folders:
        os.makedirs(folder, exist_ok=True)
        print(f"  ✓ {folder}")
    
    print("✓ All upload folders created")

def update_sample_students(conn):
    """Update sample students with department and semester"""
    cursor = conn.cursor()
    
    print("\nUpdating sample students with department and semester...")
    
    # Check if students exist
    students = cursor.execute('SELECT id, name FROM students LIMIT 2').fetchall()
    
    if students:
        # Update first student
        cursor.execute(
            'UPDATE students SET department = ?, semester = ? WHERE id = ?',
            ('Computer Science', '5', students[0][0])
        )
        print(f"  ✓ Updated {students[0][1]}: Computer Science, Semester 5")
        
        # Update second student if exists
        if len(students) > 1:
            cursor.execute(
                'UPDATE students SET department = ?, semester = ? WHERE id = ?',
                ('Computer Science', '5', students[1][0])
            )
            print(f"  ✓ Updated {students[1][1]}: Computer Science, Semester 5")
        
        conn.commit()
        print("✓ Sample students updated")
    else:
        print("⚠ No students found to update")

def verify_migration(conn):
    """Verify that all tables and columns exist"""
    cursor = conn.cursor()
    
    print("\nVerifying migration...")
    
    # Check tables
    tables = ['notices', 'notice_reads']
    for table in tables:
        if check_table_exists(cursor, table):
            print(f"✓ Table '{table}' exists")
        else:
            print(f"✗ Table '{table}' missing!")
            return False
    
    # Check student columns
    cursor.execute("PRAGMA table_info(students)")
    columns = [column[1] for column in cursor.fetchall()]
    
    for col in ['department', 'semester']:
        if col in columns:
            print(f"✓ Column '{col}' exists in students table")
        else:
            print(f"✗ Column '{col}' missing in students table!")
            return False
    
    # Check indexes
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_notice%'")
    indexes = cursor.fetchall()
    print(f"✓ Found {len(indexes)} notice-related indexes")
    
    # Check upload folders
    if os.path.exists('static/uploads/notices'):
        print("✓ Upload folders exist")
    else:
        print("✗ Upload folders missing!")
        return False
    
    print("\n✓ Migration verification complete!")
    return True

def main():
    """Main migration function"""
    print("=" * 60)
    print("  NOTICE & TIMETABLE SYSTEM MIGRATION")
    print("=" * 60)
    print()
    
    if not os.path.exists(DATABASE):
        print(f"✗ Database file '{DATABASE}' not found!")
        print("  Please run the application first to create the database.")
        return
    
    # Backup database
    print("Step 1: Backing up database...")
    backup_file = backup_database()
    print()
    
    # Connect to database
    print("Step 2: Connecting to database...")
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    print("✓ Connected to database")
    print()
    
    try:
        # Run migrations
        print("Step 3: Running migrations...")
        print("-" * 60)
        
        changes_made = False
        
        if add_student_columns(conn):
            changes_made = True
        
        if create_notices_table(conn):
            changes_made = True
        
        if create_notice_reads_table(conn):
            changes_made = True
        
        create_indexes(conn)
        changes_made = True
        
        print("-" * 60)
        print()
        
        # Create upload folders
        print("Step 4: Creating upload folders...")
        create_upload_folders()
        print()
        
        # Update sample data
        print("Step 5: Updating sample data...")
        update_sample_students(conn)
        print()
        
        if not changes_made:
            print("✓ Database is already up to date!")
        else:
            print("✓ All migrations completed successfully!")
        
        # Verify migration
        print()
        if verify_migration(conn):
            print()
            print("=" * 60)
            print("  MIGRATION SUCCESSFUL!")
            print("=" * 60)
            print()
            print("Next steps:")
            print("1. Update app_notifications.py with notice routes")
            print("2. Copy routes from app_notices_extension.py")
            print("3. Run: python app_notifications.py")
            print("4. Login as admin to upload notices")
            print()
            if backup_file:
                print(f"Note: Backup saved as '{backup_file}'")
                print("      You can restore it if needed")
        else:
            print()
            print("✗ Migration verification failed!")
            print("  Please check the errors above")
            if backup_file:
                print(f"  You can restore from backup: {backup_file}")
    
    except Exception as e:
        print()
        print(f"✗ Migration failed with error: {e}")
        print()
        if backup_file:
            print(f"Database backup available at: {backup_file}")
            print("You can restore it if needed")
        conn.rollback()
    
    finally:
        conn.close()
        print()

if __name__ == '__main__':
    main()
