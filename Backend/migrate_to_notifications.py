"""
Migration Script: Add Notification System to Existing Database
Run this script to add notification tables to your existing database
"""

import sqlite3
import os
from datetime import datetime

DATABASE = 'database.db'

def backup_database():
    """Create a backup of the current database"""
    if os.path.exists(DATABASE):
        backup_name = f'database_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
        import shutil
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

def add_notifications_table(conn):
    """Add notifications table to database"""
    cursor = conn.cursor()
    
    if check_table_exists(cursor, 'notifications'):
        print("⚠ Notifications table already exists, skipping...")
        return False
    
    print("Creating notifications table...")
    cursor.execute('''
        CREATE TABLE notifications (
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
    
    print("Creating index for faster queries...")
    cursor.execute('''
        CREATE INDEX idx_notifications_student 
        ON notifications(student_id, is_read, created_at DESC)
    ''')
    
    conn.commit()
    print("✓ Notifications table created successfully")
    return True

def add_admin_table(conn):
    """Add admin table if it doesn't exist"""
    cursor = conn.cursor()
    
    if check_table_exists(cursor, 'admin'):
        print("⚠ Admin table already exists, skipping...")
        return False
    
    print("Creating admin table...")
    cursor.execute('''
        CREATE TABLE admin (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    print("✓ Admin table created successfully")
    return True

def add_result_status_table(conn):
    """Add result_status table if it doesn't exist"""
    cursor = conn.cursor()
    
    if check_table_exists(cursor, 'result_status'):
        print("⚠ Result status table already exists, skipping...")
        return False
    
    print("Creating result_status table...")
    cursor.execute('''
        CREATE TABLE result_status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            exam TEXT UNIQUE NOT NULL,
            is_result_declared INTEGER DEFAULT 0,
            declared_by INTEGER,
            declared_at TIMESTAMP,
            FOREIGN KEY (declared_by) REFERENCES admin (id)
        )
    ''')
    
    conn.commit()
    print("✓ Result status table created successfully")
    return True

def add_is_published_column(conn):
    """Add is_published column to marks table"""
    cursor = conn.cursor()
    
    # Check if column already exists
    cursor.execute("PRAGMA table_info(marks)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'is_published' in columns:
        print("⚠ is_published column already exists in marks table, skipping...")
        return False
    
    print("Adding is_published column to marks table...")
    cursor.execute('ALTER TABLE marks ADD COLUMN is_published INTEGER DEFAULT 0')
    
    conn.commit()
    print("✓ is_published column added successfully")
    return True

def verify_migration(conn):
    """Verify that all tables and columns exist"""
    cursor = conn.cursor()
    
    print("\nVerifying migration...")
    
    # Check tables
    tables = ['notifications', 'admin', 'result_status']
    for table in tables:
        if check_table_exists(cursor, table):
            print(f"✓ Table '{table}' exists")
        else:
            print(f"✗ Table '{table}' missing!")
            return False
    
    # Check is_published column
    cursor.execute("PRAGMA table_info(marks)")
    columns = [column[1] for column in cursor.fetchall()]
    if 'is_published' in columns:
        print("✓ Column 'is_published' exists in marks table")
    else:
        print("✗ Column 'is_published' missing in marks table!")
        return False
    
    # Check index
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_notifications_student'")
    if cursor.fetchone():
        print("✓ Index 'idx_notifications_student' exists")
    else:
        print("⚠ Index 'idx_notifications_student' missing (non-critical)")
    
    print("\n✓ Migration verification complete!")
    return True

def create_sample_notifications(conn):
    """Create sample notifications for testing"""
    cursor = conn.cursor()
    
    # Check if there are any students
    cursor.execute("SELECT id FROM students LIMIT 1")
    student = cursor.fetchone()
    
    if not student:
        print("⚠ No students found, skipping sample notifications")
        return
    
    student_id = student[0]
    
    print("\nCreating sample notifications for testing...")
    
    sample_notifications = [
        {
            'title': 'Welcome to Notification System!',
            'message': 'You will now receive real-time notifications for marks, results, and grievances.',
            'type': 'announcement'
        },
        {
            'title': 'System Update',
            'message': 'The notification system has been successfully installed and configured.',
            'type': 'notice'
        }
    ]
    
    for notif in sample_notifications:
        cursor.execute(
            '''INSERT INTO notifications (student_id, title, message, type, is_read, created_at)
               VALUES (?, ?, ?, ?, 0, CURRENT_TIMESTAMP)''',
            (student_id, notif['title'], notif['message'], notif['type'])
        )
    
    conn.commit()
    print(f"✓ Created {len(sample_notifications)} sample notifications")

def main():
    """Main migration function"""
    print("=" * 60)
    print("  NOTIFICATION SYSTEM MIGRATION")
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
        
        if add_notifications_table(conn):
            changes_made = True
        
        if add_admin_table(conn):
            changes_made = True
        
        if add_result_status_table(conn):
            changes_made = True
        
        if add_is_published_column(conn):
            changes_made = True
        
        print("-" * 60)
        print()
        
        if not changes_made:
            print("✓ Database is already up to date!")
        else:
            print("✓ All migrations completed successfully!")
        
        # Verify migration
        print()
        if verify_migration(conn):
            # Create sample notifications
            create_sample_notifications(conn)
            
            print()
            print("=" * 60)
            print("  MIGRATION SUCCESSFUL!")
            print("=" * 60)
            print()
            print("Next steps:")
            print("1. Run: python app_notifications.py")
            print("2. Login as student to see notifications")
            print("3. Test by uploading marks as faculty")
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
