#!/usr/bin/env python3
"""
Show Essential Data - Display what will be kept after cleaning
"""

import sqlite3

def show_essential_data():
    print("\n" + "="*70)
    print("  ESSENTIAL DATA IN DATABASE")
    print("="*70)
    
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 1. Students
    print("\n👨‍🎓 STUDENTS (Login Credentials):")
    print("-" * 70)
    cursor.execute("SELECT id, name, email FROM students ORDER BY name")
    students = cursor.fetchall()
    
    if students:
        for student in students:
            print(f"  ID: {student['id']}")
            print(f"  Name: {student['name']}")
            print(f"  Email: {student['email']}")
            print(f"  Password: student123 (default)")
            print()
    else:
        print("  No students found")
    
    # 2. Faculty
    print("\n👨‍🏫 FACULTY (Login Credentials):")
    print("-" * 70)
    cursor.execute("SELECT id, name, email, subject, department, employee_id FROM faculty ORDER BY name")
    faculty = cursor.fetchall()
    
    if faculty:
        for fac in faculty:
            print(f"  ID: {fac['id']}")
            print(f"  Name: {fac['name']}")
            print(f"  Email: {fac['email']}")
            print(f"  Subject: {fac['subject']}")
            print(f"  Department: {fac['department']}")
            print(f"  Employee ID: {fac['employee_id']}")
            print(f"  Password: faculty123 (default)")
            print()
    else:
        print("  No faculty found")
    
    # 3. Admins
    print("\n👨‍💼 ADMINS (Login Credentials):")
    print("-" * 70)
    cursor.execute("SELECT id, name, email FROM admin ORDER BY name")
    admins = cursor.fetchall()
    
    if admins:
        for admin in admins:
            print(f"  ID: {admin['id']}")
            print(f"  Name: {admin['name']}")
            print(f"  Email: {admin['email']}")
            print(f"  Password: admin123 (default)")
            print()
    else:
        print("  No admins found")
    
    # 4. Subjects
    print("\n📚 SUBJECTS:")
    print("-" * 70)
    cursor.execute("SELECT id, code, name FROM subjects ORDER BY code")
    subjects = cursor.fetchall()
    
    if subjects:
        for subject in subjects:
            print(f"  {subject['code']} - {subject['name']}")
    else:
        print("  No subjects found")
    
    # 5. Exams
    print("\n📝 EXAM TYPES:")
    print("-" * 70)
    cursor.execute("SELECT id, name, max_marks FROM exams ORDER BY id")
    exams = cursor.fetchall()
    
    if exams:
        for exam in exams:
            print(f"  {exam['name']} (Max Marks: {exam['max_marks']})")
    else:
        print("  No exam types found")
    
    # 6. Exam Definitions
    print("\n📋 EXAM DEFINITIONS (Subject-wise Max Marks):")
    print("-" * 70)
    cursor.execute("""
        SELECT exam_name, subject, max_marks 
        FROM exam_definitions 
        ORDER BY exam_name, subject
    """)
    exam_defs = cursor.fetchall()
    
    if exam_defs:
        current_exam = None
        for ed in exam_defs:
            if ed['exam_name'] != current_exam:
                current_exam = ed['exam_name']
                print(f"\n  {current_exam}:")
            print(f"    • {ed['subject']}: {ed['max_marks']} marks")
    else:
        print("  No exam definitions found")
    
    # Summary
    print("\n" + "="*70)
    print("  SUMMARY")
    print("="*70)
    
    cursor.execute("SELECT COUNT(*) FROM students")
    print(f"  Students: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM faculty")
    print(f"  Faculty: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM admin")
    print(f"  Admins: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM subjects")
    print(f"  Subjects: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM exams")
    print(f"  Exam Types: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM exam_definitions")
    print(f"  Exam Definitions: {cursor.fetchone()[0]}")
    
    conn.close()
    
    print("\n" + "="*70)
    print()

if __name__ == '__main__':
    show_essential_data()
