#!/usr/bin/env python3
"""
Clean Database - Remove old data, keep only:
- Login credentials (students, faculty, admin)
- Subject definitions
- Exam definitions
"""

import sqlite3
import os
from datetime import datetime

def backup_database():
    """Create backup before cleaning"""
    if os.path.exists('database.db'):
        backup_name = f'database_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
        import shutil
        shutil.copy2('database.db', backup_name)
        print(f"✅ Backup created: {backup_name}")
        return backup_name
    return None

def clean_database():
    print("\n" + "="*70)
    print("  DATABASE CLEANING")
    print("="*70)
    
    # Create backup first
    backup_file = backup_database()
    
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("\n🗑️  Cleaning old data...\n")
    
    # 1. Clear marks data
    cursor.execute("SELECT COUNT(*) FROM marks")
    marks_count = cursor.fetchone()[0]
    cursor.execute("DELETE FROM marks")
    print(f"  ✅ Deleted {marks_count} marks records")
    
    # 2. Clear answer sheets data
    cursor.execute("SELECT COUNT(*) FROM answer_sheets")
    sheets_count = cursor.fetchone()[0]
    cursor.execute("DELETE FROM answer_sheets")
    print(f"  ✅ Deleted {sheets_count} answer sheets")
    
    # 3. Clear complaints data
    cursor.execute("SELECT COUNT(*) FROM complaints")
    complaints_count = cursor.fetchone()[0]
    cursor.execute("DELETE FROM complaints")
    print(f"  ✅ Deleted {complaints_count} complaints")
    
    # 4. Clear result status (if exists)
    try:
        cursor.execute("SELECT COUNT(*) FROM result_status")
        result_count = cursor.fetchone()[0]
        cursor.execute("DELETE FROM result_status")
        print(f"  ✅ Deleted {result_count} result status records")
    except:
        print(f"  ℹ️  Result status table not found (skipped)")
    
    conn.commit()
    
    print("\n✅ Keeping essential data:\n")
    
    # Show what's kept
    cursor.execute("SELECT COUNT(*) FROM students")
    students = cursor.fetchone()[0]
    print(f"  📚 Students: {students}")
    
    cursor.execute("SELECT COUNT(*) FROM faculty")
    faculty = cursor.fetchone()[0]
    print(f"  👨‍🏫 Faculty: {faculty}")
    
    try:
        cursor.execute("SELECT COUNT(*) FROM admin")
        admins = cursor.fetchone()[0]
        print(f"  👨‍💼 Admins: {admins}")
    except:
        print(f"  👨‍💼 Admins: 0")
    
    try:
        cursor.execute("SELECT COUNT(*) FROM subjects")
        subjects = cursor.fetchone()[0]
        print(f"  📖 Subjects: {subjects}")
    except:
        print(f"  📖 Subjects: 0")
    
    try:
        cursor.execute("SELECT COUNT(*) FROM exams")
        exams = cursor.fetchone()[0]
        print(f"  📝 Exams: {exams}")
    except:
        print(f"  📝 Exams: 0")
    
    try:
        cursor.execute("SELECT COUNT(*) FROM exam_definitions")
        exam_defs = cursor.fetchone()[0]
        print(f"  📋 Exam Definitions: {exam_defs}")
    except:
        pass  # Table doesn't exist
    
    # Show login credentials
    print("\n🔑 Login Credentials:\n")
    
    print("  Students:")
    cursor.execute("SELECT name, email FROM students")
    for student in cursor.fetchall():
        print(f"    • {student['name']} - {student['email']}")
    
    print("\n  Faculty:")
    cursor.execute("SELECT name, email, subject FROM faculty")
    for fac in cursor.fetchall():
        print(f"    • {fac['name']} - {fac['email']} ({fac['subject']})")
    
    try:
        print("\n  Admins:")
        cursor.execute("SELECT name, email FROM admin")
        for admin in cursor.fetchall():
            print(f"    • {admin['name']} - {admin['email']}")
    except:
        print("\n  Admins: None found")
    
    # Show subjects
    try:
        print("\n📚 Subjects:")
        cursor.execute("SELECT code, name FROM subjects")
        for subject in cursor.fetchall():
            print(f"    • {subject['code']} - {subject['name']}")
    except:
        print("\n📚 Subjects: None configured")
    
    # Show exams
    try:
        print("\n📝 Exams:")
        cursor.execute("SELECT name, max_marks FROM exams")
        for exam in cursor.fetchall():
            print(f"    • {exam['name']} (Max: {exam['max_marks']} marks)")
    except:
        print("\n📝 Exams: None configured")
    
    conn.close()
    
    print("\n" + "="*70)
    print("  ✅ DATABASE CLEANED SUCCESSFULLY")
    print("="*70)
    print(f"\n💾 Backup saved as: {backup_file}")
    print("\n🎯 Database now contains only:")
    print("  • Login credentials (students, faculty, admin)")
    print("  • Subject definitions (if configured)")
    print("  • Exam type definitions (if configured)")
    print("\n🚀 Ready for fresh data entry!")
    print()

def show_summary():
    """Show what will be deleted and kept"""
    print("\n" + "="*70)
    print("  DATABASE CLEANING PREVIEW")
    print("="*70)
    
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    print("\n🗑️  WILL BE DELETED:\n")
    
    cursor.execute("SELECT COUNT(*) FROM marks")
    print(f"  ❌ Marks: {cursor.fetchone()[0]} records")
    
    cursor.execute("SELECT COUNT(*) FROM answer_sheets")
    print(f"  ❌ Answer Sheets: {cursor.fetchone()[0]} records")
    
    cursor.execute("SELECT COUNT(*) FROM complaints")
    print(f"  ❌ Complaints: {cursor.fetchone()[0]} records")
    
    try:
        cursor.execute("SELECT COUNT(*) FROM result_status")
        print(f"  ❌ Result Status: {cursor.fetchone()[0]} records")
    except:
        print(f"  ❌ Result Status: 0 records")
    
    print("\n✅ WILL BE KEPT:\n")
    
    cursor.execute("SELECT COUNT(*) FROM students")
    print(f"  ✅ Students: {cursor.fetchone()[0]} accounts")
    
    cursor.execute("SELECT COUNT(*) FROM faculty")
    print(f"  ✅ Faculty: {cursor.fetchone()[0]} accounts")
    
    try:
        cursor.execute("SELECT COUNT(*) FROM admin")
        print(f"  ✅ Admins: {cursor.fetchone()[0]} accounts")
    except:
        print(f"  ✅ Admins: 0 accounts")
    
    try:
        cursor.execute("SELECT COUNT(*) FROM subjects")
        print(f"  ✅ Subjects: {cursor.fetchone()[0]} definitions")
    except:
        print(f"  ✅ Subjects: 0 definitions")
    
    try:
        cursor.execute("SELECT COUNT(*) FROM exams")
        print(f"  ✅ Exams: {cursor.fetchone()[0]} types")
    except:
        print(f"  ✅ Exams: 0 types")
    
    try:
        cursor.execute("SELECT COUNT(*) FROM exam_definitions")
        print(f"  ✅ Exam Definitions: {cursor.fetchone()[0]} combinations")
    except:
        pass  # Table doesn't exist yet
    
    conn.close()
    
    print("\n" + "="*70)

if __name__ == '__main__':
    import sys
    
    # Show preview first
    show_summary()
    
    # Ask for confirmation
    print("\n⚠️  WARNING: This will delete all marks, complaints, and answer sheets!")
    print("   A backup will be created automatically.")
    
    if '--yes' in sys.argv or '-y' in sys.argv:
        confirm = 'yes'
    else:
        confirm = input("\nProceed with cleaning? (yes/no): ").lower().strip()
    
    if confirm in ['yes', 'y']:
        clean_database()
    else:
        print("\n❌ Cleaning cancelled")
        print()
