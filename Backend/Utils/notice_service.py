"""
Notice & Timetable Management Service
Handles notice/timetable creation, retrieval, and student targeting
"""

from models.database_models import get_db_connection
from datetime import datetime
import logging
import os

logger = logging.getLogger(__name__)

# Notice types
NOTICE_TYPES = {
    'TIMETABLE': 'timetable',
    'GENERAL': 'general',
    'EXAM': 'exam',
    'EVENT': 'event',
    'HOLIDAY': 'holiday',
    'URGENT': 'urgent'
}

# Target roles
TARGET_ROLES = {
    'ALL': 'all',
    'DEPARTMENT': 'department',
    'SEMESTER': 'semester',
    'CLASS': 'class'
}

class NoticeService:
    """Service for managing notices and timetables"""
    
    @staticmethod
    def create_notice(title, description, file_url, file_name, file_size, notice_type, 
                     target_role='all', department=None, semester=None, uploaded_by=None, 
                     publish_at=None):
        """
        Create a new notice or timetable
        
        Args:
            title: Notice title
            description: Notice description
            file_url: Path to uploaded PDF
            file_name: Original filename
            file_size: File size in bytes
            notice_type: Type of notice (timetable, general, etc.)
            target_role: Target audience (all, department, semester, class)
            department: Department name (if targeted)
            semester: Semester (if targeted)
            uploaded_by: Admin ID who uploaded
            publish_at: Scheduled publish time (optional)
            
        Returns:
            notice_id: ID of created notice
        """
        try:
            conn = get_db_connection()
            
            # If timetable, mark old timetables as replaced
            if notice_type == NOTICE_TYPES['TIMETABLE']:
                NoticeService._archive_old_timetables(conn, department, semester)
            
            cursor = conn.execute(
                '''INSERT INTO notices 
                   (title, description, file_url, file_name, file_size, notice_type, 
                    target_role, department, semester, uploaded_by, publish_at, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)''',
                (title, description, file_url, file_name, file_size, notice_type,
                 target_role, department, semester, uploaded_by, publish_at)
            )
            notice_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            logger.info(f"Notice created: ID={notice_id}, Type={notice_type}, Target={target_role}")
            return notice_id
        except Exception as e:
            logger.error(f"Error creating notice: {e}")
            return None
    
    @staticmethod
    def _archive_old_timetables(conn, department, semester):
        """Mark old timetables as unpublished when new one is uploaded"""
        try:
            if department and semester:
                conn.execute(
                    '''UPDATE notices 
                       SET is_published = 0 
                       WHERE notice_type = ? AND department = ? AND semester = ? AND is_published = 1''',
                    (NOTICE_TYPES['TIMETABLE'], department, semester)
                )
            elif department:
                conn.execute(
                    '''UPDATE notices 
                       SET is_published = 0 
                       WHERE notice_type = ? AND department = ? AND is_published = 1''',
                    (NOTICE_TYPES['TIMETABLE'], department)
                )
            else:
                conn.execute(
                    '''UPDATE notices 
                       SET is_published = 0 
                       WHERE notice_type = ? AND is_published = 1''',
                    (NOTICE_TYPES['TIMETABLE'],)
                )
            conn.commit()
            logger.info("Old timetables archived")
        except Exception as e:
            logger.error(f"Error archiving old timetables: {e}")
    
    @staticmethod
    def get_notices_for_student(student_id, notice_type=None, limit=50):
        """
        Get notices visible to a specific student based on their department/semester
        
        Args:
            student_id: Student ID
            notice_type: Filter by notice type (optional)
            limit: Maximum number of notices to return
            
        Returns:
            List of notices with read status
        """
        try:
            conn = get_db_connection()
            
            # Get student info
            student = conn.execute(
                'SELECT department, semester FROM students WHERE id = ?',
                (student_id,)
            ).fetchone()
            
            if not student:
                conn.close()
                return []
            
            student_dept = student['department']
            student_sem = student['semester']
            
            # Build query based on filters
            query = '''
                SELECT n.*, a.name as uploaded_by_name,
                       nr.is_read, nr.read_at
                FROM notices n
                JOIN admin a ON n.uploaded_by = a.id
                LEFT JOIN notice_reads nr ON n.id = nr.notice_id AND nr.student_id = ?
                WHERE n.is_published = 1
                AND (n.publish_at IS NULL OR n.publish_at <= CURRENT_TIMESTAMP)
                AND (
                    n.target_role = 'all'
                    OR (n.target_role = 'department' AND n.department = ?)
                    OR (n.target_role = 'semester' AND n.semester = ?)
                    OR (n.target_role = 'class' AND n.department = ? AND n.semester = ?)
                )
            '''
            
            params = [student_id, student_dept, student_sem, student_dept, student_sem]
            
            if notice_type:
                query += ' AND n.notice_type = ?'
                params.append(notice_type)
            
            query += ' ORDER BY n.created_at DESC LIMIT ?'
            params.append(limit)
            
            notices = conn.execute(query, params).fetchall()
            conn.close()
            
            return [dict(n) for n in notices]
        except Exception as e:
            logger.error(f"Error fetching notices for student: {e}")
            return []
    
    @staticmethod
    def get_all_notices(notice_type=None, limit=100):
        """Get all notices (admin view)"""
        try:
            conn = get_db_connection()
            
            query = '''
                SELECT n.*, a.name as uploaded_by_name,
                       COUNT(DISTINCT nr.student_id) as read_count
                FROM notices n
                JOIN admin a ON n.uploaded_by = a.id
                LEFT JOIN notice_reads nr ON n.id = nr.notice_id AND nr.is_read = 1
            '''
            
            params = []
            if notice_type:
                query += ' WHERE n.notice_type = ?'
                params.append(notice_type)
            
            query += ' GROUP BY n.id ORDER BY n.created_at DESC LIMIT ?'
            params.append(limit)
            
            notices = conn.execute(query, params).fetchall()
            conn.close()
            
            return [dict(n) for n in notices]
        except Exception as e:
            logger.error(f"Error fetching all notices: {e}")
            return []
    
    @staticmethod
    def get_notice_by_id(notice_id):
        """Get a specific notice by ID"""
        try:
            conn = get_db_connection()
            notice = conn.execute(
                '''SELECT n.*, a.name as uploaded_by_name
                   FROM notices n
                   JOIN admin a ON n.uploaded_by = a.id
                   WHERE n.id = ?''',
                (notice_id,)
            ).fetchone()
            conn.close()
            
            return dict(notice) if notice else None
        except Exception as e:
            logger.error(f"Error fetching notice: {e}")
            return None
    
    @staticmethod
    def mark_notice_read(notice_id, student_id):
        """Mark a notice as read by a student"""
        try:
            conn = get_db_connection()
            
            # Check if record exists
            existing = conn.execute(
                'SELECT id FROM notice_reads WHERE notice_id = ? AND student_id = ?',
                (notice_id, student_id)
            ).fetchone()
            
            if existing:
                conn.execute(
                    '''UPDATE notice_reads 
                       SET is_read = 1, read_at = CURRENT_TIMESTAMP 
                       WHERE notice_id = ? AND student_id = ?''',
                    (notice_id, student_id)
                )
            else:
                conn.execute(
                    '''INSERT INTO notice_reads (notice_id, student_id, is_read, read_at)
                       VALUES (?, ?, 1, CURRENT_TIMESTAMP)''',
                    (notice_id, student_id)
                )
            
            conn.commit()
            conn.close()
            
            logger.info(f"Notice {notice_id} marked as read by student {student_id}")
            return True
        except Exception as e:
            logger.error(f"Error marking notice as read: {e}")
            return False
    
    @staticmethod
    def increment_download_count(notice_id):
        """Increment download count for a notice"""
        try:
            conn = get_db_connection()
            conn.execute(
                'UPDATE notices SET download_count = download_count + 1 WHERE id = ?',
                (notice_id,)
            )
            conn.commit()
            conn.close()
            
            logger.info(f"Download count incremented for notice {notice_id}")
            return True
        except Exception as e:
            logger.error(f"Error incrementing download count: {e}")
            return False
    
    @staticmethod
    def get_unread_count(student_id, notice_type=None):
        """Get count of unread notices for a student"""
        try:
            conn = get_db_connection()
            
            # Get student info
            student = conn.execute(
                'SELECT department, semester FROM students WHERE id = ?',
                (student_id,)
            ).fetchone()
            
            if not student:
                conn.close()
                return 0
            
            student_dept = student['department']
            student_sem = student['semester']
            
            query = '''
                SELECT COUNT(*) FROM notices n
                LEFT JOIN notice_reads nr ON n.id = nr.notice_id AND nr.student_id = ?
                WHERE n.is_published = 1
                AND (n.publish_at IS NULL OR n.publish_at <= CURRENT_TIMESTAMP)
                AND (nr.is_read IS NULL OR nr.is_read = 0)
                AND (
                    n.target_role = 'all'
                    OR (n.target_role = 'department' AND n.department = ?)
                    OR (n.target_role = 'semester' AND n.semester = ?)
                    OR (n.target_role = 'class' AND n.department = ? AND n.semester = ?)
                )
            '''
            
            params = [student_id, student_dept, student_sem, student_dept, student_sem]
            
            if notice_type:
                query += ' AND n.notice_type = ?'
                params.append(notice_type)
            
            count = conn.execute(query, params).fetchone()[0]
            conn.close()
            
            return count
        except Exception as e:
            logger.error(f"Error getting unread count: {e}")
            return 0
    
    @staticmethod
    def update_notice(notice_id, title=None, description=None, target_role=None, 
                     department=None, semester=None):
        """Update notice details"""
        try:
            conn = get_db_connection()
            
            updates = []
            params = []
            
            if title:
                updates.append('title = ?')
                params.append(title)
            if description is not None:
                updates.append('description = ?')
                params.append(description)
            if target_role:
                updates.append('target_role = ?')
                params.append(target_role)
            if department is not None:
                updates.append('department = ?')
                params.append(department)
            if semester is not None:
                updates.append('semester = ?')
                params.append(semester)
            
            if not updates:
                conn.close()
                return False
            
            params.append(notice_id)
            query = f"UPDATE notices SET {', '.join(updates)} WHERE id = ?"
            
            conn.execute(query, params)
            conn.commit()
            conn.close()
            
            logger.info(f"Notice {notice_id} updated")
            return True
        except Exception as e:
            logger.error(f"Error updating notice: {e}")
            return False
    
    @staticmethod
    def delete_notice(notice_id):
        """Delete a notice and its file"""
        try:
            conn = get_db_connection()
            
            # Get file path
            notice = conn.execute(
                'SELECT file_url FROM notices WHERE id = ?',
                (notice_id,)
            ).fetchone()
            
            if notice:
                # Delete file
                file_path = notice['file_url']
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.info(f"Deleted file: {file_path}")
                
                # Delete notice reads
                conn.execute('DELETE FROM notice_reads WHERE notice_id = ?', (notice_id,))
                
                # Delete notice
                conn.execute('DELETE FROM notices WHERE id = ?', (notice_id,))
                conn.commit()
                
                logger.info(f"Notice {notice_id} deleted")
            
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error deleting notice: {e}")
            return False
    
    @staticmethod
    def get_targeted_students(target_role, department=None, semester=None):
        """
        Get list of student IDs based on targeting criteria
        
        Args:
            target_role: 'all', 'department', 'semester', or 'class'
            department: Department name (if targeted)
            semester: Semester (if targeted)
            
        Returns:
            List of student IDs
        """
        try:
            conn = get_db_connection()
            
            if target_role == 'all':
                students = conn.execute('SELECT id FROM students').fetchall()
            elif target_role == 'department':
                students = conn.execute(
                    'SELECT id FROM students WHERE department = ?',
                    (department,)
                ).fetchall()
            elif target_role == 'semester':
                students = conn.execute(
                    'SELECT id FROM students WHERE semester = ?',
                    (semester,)
                ).fetchall()
            elif target_role == 'class':
                students = conn.execute(
                    'SELECT id FROM students WHERE department = ? AND semester = ?',
                    (department, semester)
                ).fetchall()
            else:
                students = []
            
            conn.close()
            
            return [s['id'] for s in students]
        except Exception as e:
            logger.error(f"Error getting targeted students: {e}")
            return []
    
    @staticmethod
    def get_notice_statistics():
        """Get statistics for admin dashboard"""
        try:
            conn = get_db_connection()
            
            total_notices = conn.execute('SELECT COUNT(*) FROM notices').fetchone()[0]
            total_timetables = conn.execute(
                'SELECT COUNT(*) FROM notices WHERE notice_type = ?',
                (NOTICE_TYPES['TIMETABLE'],)
            ).fetchone()[0]
            total_downloads = conn.execute(
                'SELECT SUM(download_count) FROM notices'
            ).fetchone()[0] or 0
            
            # Get read percentage
            total_reads = conn.execute(
                'SELECT COUNT(*) FROM notice_reads WHERE is_read = 1'
            ).fetchone()[0]
            total_students = conn.execute('SELECT COUNT(*) FROM students').fetchone()[0]
            
            read_percentage = 0
            if total_notices > 0 and total_students > 0:
                expected_reads = total_notices * total_students
                read_percentage = (total_reads / expected_reads * 100) if expected_reads > 0 else 0
            
            # Recent uploads
            recent = conn.execute(
                '''SELECT n.*, a.name as uploaded_by_name
                   FROM notices n
                   JOIN admin a ON n.uploaded_by = a.id
                   ORDER BY n.created_at DESC LIMIT 5'''
            ).fetchall()
            
            conn.close()
            
            return {
                'total_notices': total_notices,
                'total_timetables': total_timetables,
                'total_downloads': total_downloads,
                'read_percentage': round(read_percentage, 2),
                'recent_uploads': [dict(r) for r in recent]
            }
        except Exception as e:
            logger.error(f"Error getting notice statistics: {e}")
            return {}
