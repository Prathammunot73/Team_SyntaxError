"""
AI-Based Assignment Service with Early Submission Reward System
Handles assignment creation, submission tracking, and bonus calculation
"""

import uuid
from datetime import datetime
from models.database_models import get_db_connection


class RewardType:
    """Reward calculation strategies"""
    FIXED = 'fixed'
    TIER = 'tier'
    SCALING = 'scaling'


class AssignmentService:
    """Service for managing assignments and calculating AI-based bonuses"""
    
    @staticmethod
    def create_assignment(title, description, subject, deadline, max_bonus_marks, 
                         reward_type, created_by, submission_mode='offline'):
        """
        Create a new assignment
        
        Args:
            title (str): Assignment title
            description (str): Assignment description
            subject (str): Subject name
            deadline (datetime): Submission deadline
            max_bonus_marks (float): Maximum bonus marks
            reward_type (str): Reward calculation type (fixed/tier/scaling)
            created_by (int): Faculty ID
            submission_mode (str): 'online' or 'offline' submission
            
        Returns:
            str: Assignment ID or None if failed
        """
        try:
            assignment_id = str(uuid.uuid4())
            conn = get_db_connection()
            
            conn.execute('''
                INSERT INTO assignments 
                (id, title, description, subject, deadline, max_bonus_marks, 
                 reward_type, submission_mode, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (assignment_id, title, description, subject, deadline, 
                  max_bonus_marks, reward_type, submission_mode, created_by))
            
            conn.commit()
            conn.close()
            return assignment_id
        except Exception as e:
            print(f"Error creating assignment: {e}")
            return None
    
    @staticmethod
    def get_assignment_by_id(assignment_id):
        """Get assignment details by ID"""
        conn = get_db_connection()
        assignment = conn.execute(
            '''SELECT a.*, f.name as faculty_name, f.subject as faculty_subject
               FROM assignments a
               JOIN faculty f ON a.created_by = f.id
               WHERE a.id = ?''',
            (assignment_id,)
        ).fetchone()
        conn.close()
        return assignment
    
    @staticmethod
    def get_assignments_by_faculty(faculty_id):
        """Get all assignments created by a faculty member"""
        conn = get_db_connection()
        assignments = conn.execute(
            '''SELECT a.*, 
                      COUNT(DISTINCT s.id) as submission_count,
                      COUNT(DISTINCT CASE WHEN s.is_verified = 1 THEN s.id END) as verified_count
               FROM assignments a
               LEFT JOIN submissions s ON a.id = s.assignment_id
               WHERE a.created_by = ?
               GROUP BY a.id
               ORDER BY a.created_at DESC''',
            (faculty_id,)
        ).fetchall()
        conn.close()
        return assignments
    
    @staticmethod
    def get_active_assignments(subject=None):
        """Get all active assignments, optionally filtered by subject"""
        conn = get_db_connection()
        
        if subject:
            assignments = conn.execute(
                '''SELECT a.*, f.name as faculty_name
                   FROM assignments a
                   JOIN faculty f ON a.created_by = f.id
                   WHERE a.is_active = 1 AND a.subject = ?
                   ORDER BY a.deadline ASC''',
                (subject,)
            ).fetchall()
        else:
            assignments = conn.execute(
                '''SELECT a.*, f.name as faculty_name
                   FROM assignments a
                   JOIN faculty f ON a.created_by = f.id
                   WHERE a.is_active = 1
                   ORDER BY a.deadline ASC'''
            ).fetchall()
        
        conn.close()
        return assignments
    
    @staticmethod
    def submit_assignment(assignment_id, student_id, file_path=None):
        """
        Submit an assignment and calculate AI bonus
        
        Args:
            assignment_id (str): Assignment ID
            student_id (int): Student ID
            file_path (str): Path to uploaded file (optional)
            
        Returns:
            tuple: (success, message, bonus_marks)
        """
        try:
            conn = get_db_connection()
            
            # Check if already submitted
            existing = conn.execute(
                'SELECT id FROM submissions WHERE assignment_id = ? AND student_id = ?',
                (assignment_id, student_id)
            ).fetchone()
            
            if existing:
                conn.close()
                return False, "Assignment already submitted", 0
            
            # Get assignment details
            assignment = conn.execute(
                'SELECT * FROM assignments WHERE id = ? AND is_active = 1',
                (assignment_id,)
            ).fetchone()
            
            if not assignment:
                conn.close()
                return False, "Assignment not found or inactive", 0
            
            # Calculate AI bonus
            submission_time = datetime.now()
            ai_bonus = AssignmentService._calculate_ai_bonus(
                assignment, submission_time
            )
            
            # Create submission
            submission_id = str(uuid.uuid4())
            conn.execute('''
                INSERT INTO submissions 
                (id, assignment_id, student_id, submission_time, file_path, ai_bonus_marks)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (submission_id, assignment_id, student_id, submission_time, 
                  file_path, ai_bonus))
            
            conn.commit()
            conn.close()
            
            return True, "Assignment submitted successfully", ai_bonus
        except Exception as e:
            print(f"Error submitting assignment: {e}")
            return False, f"Error: {str(e)}", 0
    
    @staticmethod
    def _calculate_ai_bonus(assignment, submission_time):
        """
        Calculate AI bonus based on reward type
        
        Args:
            assignment: Assignment database row
            submission_time (datetime): Time of submission
            
        Returns:
            float: Calculated bonus marks
        """
        deadline = datetime.fromisoformat(assignment['deadline'])
        created_at = datetime.fromisoformat(assignment['created_at'])
        max_bonus = assignment['max_bonus_marks']
        reward_type = assignment['reward_type']
        
        # Check if submitted after deadline
        if submission_time > deadline:
            return 0.0
        
        # Calculate time metrics
        total_time = (deadline - created_at).total_seconds()
        time_taken = (submission_time - created_at).total_seconds()
        remaining_time = (deadline - submission_time).total_seconds()
        
        if total_time <= 0:
            return 0.0
        
        # Calculate based on reward type
        if reward_type == RewardType.FIXED:
            # Fixed reward: Full bonus if before deadline
            return max_bonus
        
        elif reward_type == RewardType.TIER:
            # Tier-based reward
            time_percentage = (time_taken / total_time) * 100
            
            if time_percentage <= 25:
                return max_bonus  # 100% bonus
            elif time_percentage <= 50:
                return max_bonus * 0.75  # 75% bonus
            elif time_percentage <= 75:
                return max_bonus * 0.50  # 50% bonus
            else:
                return max_bonus * 0.25  # 25% bonus
        
        elif reward_type == RewardType.SCALING:
            # Linear scaling: Bonus proportional to remaining time
            bonus = max_bonus * (remaining_time / total_time)
            return round(bonus, 2)
        
        return 0.0
    
    @staticmethod
    def get_submissions_for_assignment(assignment_id):
        """Get all submissions for an assignment with student details"""
        conn = get_db_connection()
        submissions = conn.execute('''
            SELECT s.*, st.name as student_name, st.email as student_email,
                   f.name as verified_by_name
            FROM submissions s
            JOIN students st ON s.student_id = st.id
            LEFT JOIN faculty f ON s.verified_by = f.id
            WHERE s.assignment_id = ?
            ORDER BY s.submission_time ASC
        ''', (assignment_id,)).fetchall()
        conn.close()
        return submissions
    
    @staticmethod
    def get_student_submissions(student_id):
        """Get all submissions by a student"""
        conn = get_db_connection()
        submissions = conn.execute('''
            SELECT s.*, a.title as assignment_title, a.subject, a.deadline,
                   a.max_bonus_marks, f.name as faculty_name
            FROM submissions s
            JOIN assignments a ON s.assignment_id = a.id
            JOIN faculty f ON a.created_by = f.id
            WHERE s.student_id = ?
            ORDER BY s.submission_time DESC
        ''', (student_id,)).fetchall()
        conn.close()
        return submissions
    
    @staticmethod
    def verify_submission(submission_id, faculty_id, approve=True, 
                         manual_bonus=None, notes=None):
        """
        Verify a submission and optionally override bonus
        
        Args:
            submission_id (str): Submission ID
            faculty_id (int): Faculty ID performing verification
            approve (bool): Whether to approve the submission
            manual_bonus (float): Manual bonus override (optional)
            notes (str): Teacher notes (optional)
            
        Returns:
            tuple: (success, message)
        """
        try:
            conn = get_db_connection()
            
            # Get submission details
            submission = conn.execute(
                'SELECT * FROM submissions WHERE id = ?',
                (submission_id,)
            ).fetchone()
            
            if not submission:
                conn.close()
                return False, "Submission not found"
            
            # Determine final bonus
            if manual_bonus is not None:
                final_bonus = manual_bonus
            else:
                final_bonus = submission['ai_bonus_marks'] if approve else 0
            
            # Update submission
            conn.execute('''
                UPDATE submissions
                SET is_verified = ?, teacher_final_bonus = ?, teacher_notes = ?,
                    verified_by = ?, verified_at = ?
                WHERE id = ?
            ''', (1 if approve else 0, final_bonus, notes, faculty_id, 
                  datetime.now(), submission_id))
            
            # Log the change
            conn.execute('''
                INSERT INTO assignment_marks_log
                (submission_id, student_id, action, old_value, new_value, 
                 changed_by, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (submission_id, submission['student_id'], 
                  'VERIFIED' if approve else 'REJECTED',
                  submission['ai_bonus_marks'], final_bonus, faculty_id, notes))
            
            # If approved, add to internal marks
            if approve:
                conn.execute('''
                    UPDATE students
                    SET internal_marks = COALESCE(internal_marks, 0) + ?
                    WHERE id = ?
                ''', (final_bonus, submission['student_id']))
            
            conn.commit()
            conn.close()
            
            return True, "Submission verified successfully"
        except Exception as e:
            print(f"Error verifying submission: {e}")
            return False, f"Error: {str(e)}"
    
    @staticmethod
    def bulk_verify_submissions(submission_ids, faculty_id):
        """Bulk verify multiple submissions"""
        success_count = 0
        for submission_id in submission_ids:
            success, _ = AssignmentService.verify_submission(
                submission_id, faculty_id, approve=True
            )
            if success:
                success_count += 1
        
        return success_count, len(submission_ids)
    
    @staticmethod
    def get_assignment_statistics(assignment_id):
        """Get statistics for an assignment"""
        conn = get_db_connection()
        
        stats = {
            'total_submissions': 0,
            'verified_submissions': 0,
            'pending_submissions': 0,
            'avg_bonus': 0,
            'total_bonus_awarded': 0,
            'early_submissions': 0,
            'late_submissions': 0
        }
        
        # Get assignment
        assignment = conn.execute(
            'SELECT * FROM assignments WHERE id = ?',
            (assignment_id,)
        ).fetchone()
        
        if not assignment:
            conn.close()
            return stats
        
        deadline = datetime.fromisoformat(assignment['deadline'])
        
        # Get submissions
        submissions = conn.execute(
            'SELECT * FROM submissions WHERE assignment_id = ?',
            (assignment_id,)
        ).fetchall()
        
        stats['total_submissions'] = len(submissions)
        
        for sub in submissions:
            if sub['is_verified']:
                stats['verified_submissions'] += 1
                if sub['teacher_final_bonus']:
                    stats['total_bonus_awarded'] += sub['teacher_final_bonus']
            else:
                stats['pending_submissions'] += 1
            
            sub_time = datetime.fromisoformat(sub['submission_time'])
            if sub_time <= deadline:
                stats['early_submissions'] += 1
            else:
                stats['late_submissions'] += 1
        
        if stats['verified_submissions'] > 0:
            stats['avg_bonus'] = round(
                stats['total_bonus_awarded'] / stats['verified_submissions'], 2
            )
        
        conn.close()
        return stats
    
    @staticmethod
    def deactivate_assignment(assignment_id):
        """Deactivate an assignment"""
        try:
            conn = get_db_connection()
            conn.execute(
                'UPDATE assignments SET is_active = 0 WHERE id = ?',
                (assignment_id,)
            )
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error deactivating assignment: {e}")
            return False
