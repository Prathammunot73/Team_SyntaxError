"""
Migration script to add submission_mode column to assignments table
Run this once to update existing database
"""

import sqlite3

def migrate_database():
    """Add submission_mode column to assignments table"""
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        # Check if column already exists
        cursor.execute("PRAGMA table_info(assignments)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'submission_mode' not in columns:
            print("Adding submission_mode column to assignments table...")
            cursor.execute('''
                ALTER TABLE assignments 
                ADD COLUMN submission_mode TEXT DEFAULT 'offline'
            ''')
            conn.commit()
            print("✓ Column added successfully!")
            
            # Update existing assignments to offline mode
            cursor.execute("UPDATE assignments SET submission_mode = 'offline' WHERE submission_mode IS NULL")
            conn.commit()
            print("✓ Existing assignments set to offline mode")
        else:
            print("✓ Column already exists, no migration needed")
        
        conn.close()
        print("\n✅ Migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    print("=" * 60)
    print("DATABASE MIGRATION: Add submission_mode column")
    print("=" * 60)
    print()
    migrate_database()
