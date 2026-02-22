"""
Migration script to add event calendar tables
Run this once to update existing database
"""

import sqlite3

def migrate_database():
    """Add event calendar tables to database"""
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        print("Adding event calendar tables...")
        
        # Check if exam_events table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='exam_events'")
        if not cursor.fetchone():
            print("Creating exam_events table...")
            cursor.execute('''
                CREATE TABLE exam_events (
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
            print("✓ exam_events table created")
        else:
            print("✓ exam_events table already exists")
        
        # Check if event_notifications table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='event_notifications'")
        if not cursor.fetchone():
            print("Creating event_notifications table...")
            cursor.execute('''
                CREATE TABLE event_notifications (
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
            print("✓ event_notifications table created")
        else:
            print("✓ event_notifications table already exists")
        
        # Create indexes
        print("Creating indexes...")
        
        try:
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_exam_events_date 
                ON exam_events(event_date, is_active)
            ''')
            print("✓ idx_exam_events_date index created")
        except:
            print("✓ idx_exam_events_date index already exists")
        
        try:
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_exam_events_target 
                ON exam_events(target_audience, semester, department)
            ''')
            print("✓ idx_exam_events_target index created")
        except:
            print("✓ idx_exam_events_target index already exists")
        
        try:
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_event_notifications 
                ON event_notifications(event_id, student_id)
            ''')
            print("✓ idx_event_notifications index created")
        except:
            print("✓ idx_event_notifications index already exists")
        
        # Add department and semester columns to students if they don't exist
        try:
            cursor.execute('ALTER TABLE students ADD COLUMN department TEXT')
            print("✓ Added department column to students")
        except sqlite3.OperationalError:
            print("✓ Department column already exists in students")
        
        try:
            cursor.execute('ALTER TABLE students ADD COLUMN semester TEXT')
            print("✓ Added semester column to students")
        except sqlite3.OperationalError:
            print("✓ Semester column already exists in students")
        
        conn.commit()
        conn.close()
        
        print("\n✅ Event calendar migration completed successfully!")
        print("\nNew features available:")
        print("- Admin can create events at /admin/events")
        print("- Students can view calendar at /student/calendar")
        print("- Automatic email notifications")
        print("- Real-time updates via WebSocket")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    print("=" * 60)
    print("DATABASE MIGRATION: Add Event Calendar Tables")
    print("=" * 60)
    print()
    migrate_database()