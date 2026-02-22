"""
Real-time Notification Service
Handles notification creation, storage, and WebSocket broadcasting
"""

from models.database_models import get_db_connection
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Notification types
NOTIFICATION_TYPES = {
    'MARKS': 'marks',
    'RESULT': 'result',
    'GRIEVANCE': 'grievance',
    'NOTICE': 'notice',
    'ANNOUNCEMENT': 'announcement',
    'PDF_UPLOAD': 'pdf_upload'
}

class NotificationService:
    """Service for managing notifications"""
    
    @staticmethod
    def create_notification(student_id, title, message, notification_type, related_id=None):
        """
        Create a new notification in the database
        
        Args:
            student_id: ID of the student to notify
            title: Notification title
            message: Notification message
            notification_type: Type of notification (marks, result, grievance, etc.)
            related_id: Optional ID of related entity (mark_id, complaint_id, etc.)
            
        Returns:
            notification_id: ID of created notification
        """
        try:
            conn = get_db_connection()
            cursor = conn.execute(
                '''INSERT INTO notifications (student_id, title, message, type, related_id, is_read, created_at)
                   VALUES (?, ?, ?, ?, ?, 0, CURRENT_TIMESTAMP)''',
                (student_id, title, message, notification_type, related_id)
            )
            notification_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            logger.info(f"Notification created: ID={notification_id}, Student={student_id}, Type={notification_type}")
            return notification_id
        except Exception as e:
            logger.error(f"Error creating notification: {e}")
            return None
    
    @staticmethod
    def get_unread_notifications(student_id, limit=10):
        """Get unread notifications for a student"""
        try:
            conn = get_db_connection()
            notifications = conn.execute(
                '''SELECT * FROM notifications 
                   WHERE student_id = ? AND is_read = 0 
                   ORDER BY created_at DESC LIMIT ?''',
                (student_id, limit)
            ).fetchall()
            conn.close()
            
            return [dict(n) for n in notifications]
        except Exception as e:
            logger.error(f"Error fetching unread notifications: {e}")
            return []
    
    @staticmethod
    def get_all_notifications(student_id, limit=50):
        """Get all notifications for a student"""
        try:
            conn = get_db_connection()
            notifications = conn.execute(
                '''SELECT * FROM notifications 
                   WHERE student_id = ? 
                   ORDER BY created_at DESC LIMIT ?''',
                (student_id, limit)
            ).fetchall()
            conn.close()
            
            return [dict(n) for n in notifications]
        except Exception as e:
            logger.error(f"Error fetching notifications: {e}")
            return []
    
    @staticmethod
    def get_unread_count(student_id):
        """Get count of unread notifications"""
        try:
            conn = get_db_connection()
            count = conn.execute(
                'SELECT COUNT(*) FROM notifications WHERE student_id = ? AND is_read = 0',
                (student_id,)
            ).fetchone()[0]
            conn.close()
            
            return count
        except Exception as e:
            logger.error(f"Error getting unread count: {e}")
            return 0
    
    @staticmethod
    def mark_as_read(notification_id, student_id):
        """Mark a notification as read"""
        try:
            conn = get_db_connection()
            conn.execute(
                'UPDATE notifications SET is_read = 1 WHERE id = ? AND student_id = ?',
                (notification_id, student_id)
            )
            conn.commit()
            conn.close()
            
            logger.info(f"Notification marked as read: ID={notification_id}")
            return True
        except Exception as e:
            logger.error(f"Error marking notification as read: {e}")
            return False
    
    @staticmethod
    def mark_all_as_read(student_id):
        """Mark all notifications as read for a student"""
        try:
            conn = get_db_connection()
            conn.execute(
                'UPDATE notifications SET is_read = 1 WHERE student_id = ? AND is_read = 0',
                (student_id,)
            )
            conn.commit()
            conn.close()
            
            logger.info(f"All notifications marked as read for student: {student_id}")
            return True
        except Exception as e:
            logger.error(f"Error marking all notifications as read: {e}")
            return False
    
    @staticmethod
    def delete_notification(notification_id, student_id):
        """Delete a notification"""
        try:
            conn = get_db_connection()
            conn.execute(
                'DELETE FROM notifications WHERE id = ? AND student_id = ?',
                (notification_id, student_id)
            )
            conn.commit()
            conn.close()
            
            logger.info(f"Notification deleted: ID={notification_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting notification: {e}")
            return False
    
    @staticmethod
    def notify_marks_uploaded(student_id, subject, exam, marks, faculty_name):
        """Create notification for marks upload"""
        title = f"New Marks: {subject}"
        message = f"Your marks for {subject} - {exam} have been uploaded by {faculty_name}. Score: {marks}"
        return NotificationService.create_notification(
            student_id, title, message, NOTIFICATION_TYPES['MARKS']
        )
    
    @staticmethod
    def notify_result_published(student_id, exam):
        """Create notification for result publication"""
        title = f"Results Published: {exam}"
        message = f"The results for {exam} have been officially published. Check your results now!"
        return NotificationService.create_notification(
            student_id, title, message, NOTIFICATION_TYPES['RESULT']
        )
    
    @staticmethod
    def notify_grievance_update(student_id, complaint_id, status, subject, exam):
        """Create notification for grievance status update"""
        title = f"Grievance Update: {subject}"
        message = f"Your grievance for {subject} - {exam} has been {status.lower()}"
        return NotificationService.create_notification(
            student_id, title, message, NOTIFICATION_TYPES['GRIEVANCE'], complaint_id
        )
    
    @staticmethod
    def notify_pdf_uploaded(student_id, subject, exam):
        """Create notification for answer sheet upload"""
        title = f"Answer Sheet Available: {subject}"
        message = f"Your answer sheet for {subject} - {exam} is now available for viewing"
        return NotificationService.create_notification(
            student_id, title, message, NOTIFICATION_TYPES['PDF_UPLOAD']
        )
    
    @staticmethod
    def broadcast_announcement(title, message, student_ids=None):
        """
        Broadcast announcement to multiple students
        
        Args:
            title: Announcement title
            message: Announcement message
            student_ids: List of student IDs (None = all students)
            
        Returns:
            count: Number of notifications created
        """
        try:
            conn = get_db_connection()
            
            # Get all student IDs if not specified
            if student_ids is None:
                students = conn.execute('SELECT id FROM students').fetchall()
                student_ids = [s['id'] for s in students]
            
            # Create notification for each student
            count = 0
            for student_id in student_ids:
                cursor = conn.execute(
                    '''INSERT INTO notifications (student_id, title, message, type, is_read, created_at)
                       VALUES (?, ?, ?, ?, 0, CURRENT_TIMESTAMP)''',
                    (student_id, title, message, NOTIFICATION_TYPES['ANNOUNCEMENT'])
                )
                count += 1
            
            conn.commit()
            conn.close()
            
            logger.info(f"Broadcast announcement sent to {count} students")
            return count
        except Exception as e:
            logger.error(f"Error broadcasting announcement: {e}")
            return 0
    
    @staticmethod
    def get_notification_stats():
        """Get notification statistics for admin dashboard"""
        try:
            conn = get_db_connection()
            
            total_sent = conn.execute('SELECT COUNT(*) FROM notifications').fetchone()[0]
            total_read = conn.execute('SELECT COUNT(*) FROM notifications WHERE is_read = 1').fetchone()[0]
            total_unread = conn.execute('SELECT COUNT(*) FROM notifications WHERE is_read = 0').fetchone()[0]
            
            # Get notifications by type
            by_type = conn.execute('''
                SELECT type, COUNT(*) as count 
                FROM notifications 
                GROUP BY type
            ''').fetchall()
            
            conn.close()
            
            return {
                'total_sent': total_sent,
                'total_read': total_read,
                'total_unread': total_unread,
                'by_type': {row['type']: row['count'] for row in by_type}
            }
        except Exception as e:
            logger.error(f"Error getting notification stats: {e}")
            return {}
