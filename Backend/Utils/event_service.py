"""
Centralized Exam & Event Calendar Service
Handles event CRUD operations, email notifications, and real-time updates
"""

import uuid
from datetime import datetime, date, time
from models.database_models import get_db_connection
from utils.email_service import EmailService
from utils.websocket_handler import WebSocketHandler


class EventType:
    """Event type constants"""
    EXAM = 'exam'
    SEMINAR = 'seminar'
    PRACTICAL = 'practical'
    ASSIGNMENT = 'assignment'
    HOLIDAY = 'holiday'
    MEETING = 'meeting'


class TargetAudience:
    """Target audience constants"""
    ALL = 'all'
    SEMESTER = 'semester'
    DEPARTMENT = 'department'
    CLASS = 'class'


class EventService:
    """Service for managing exam events and calendar"""
    
    @staticmethod
    def create_event(title, description, event_date, start_time, end_time, 
                    event_type, semester=None, department=None, 
                    target_audience='all', created_by=None):
        """
        Create a new exam/event
        
        Args:
            title (str): Event title
            description (str): Event description
            event_date (str): Event date (YYYY-MM-DD)
            start_time (str): Start time (HH:MM)
            end_time (str): End time (HH:MM)
            event_type (str): Type of event
            semester (str): Target semester (optional)
            department (str): Target department (optional)
            target_audience (str): Target audience type
            created_by (int): Admin ID
            
        Returns:
            str: Event ID or None if failed
        """
        try:
            event_id = str(uuid.uuid4())
            conn = get_db_connection()
            
            conn.execute('''
                INSERT INTO exam_events 
                (id, title, description, event_date, start_time, end_time,
                 event_type, semester, department, target_audience, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (event_id, title, description, event_date, start_time, end_time,
                  event_type, semester, department, target_audience, created_by))
            
            conn.commit()
            conn.close()
            
            # Send email notifications asynchronously
            EventService._send_event_notifications(event_id, 'created')
            
            # Send real-time update
            EventService._broadcast_event_update(event_id, 'created')
            
            return event_id
        except Exception as e:
            print(f"Error creating event: {e}")
            return None
    
    @staticmethod
    def get_event_by_id(event_id):
        """Get event details by ID"""
        conn = get_db_connection()
        event = conn.execute(
            '''SELECT e.*, a.name as created_by_name
               FROM exam_events e
               JOIN admin a ON e.created_by = a.id
               WHERE e.id = ? AND e.is_active = 1''',
            (event_id,)
        ).fetchone()
        conn.close()
        return event
    
    @staticmethod
    def get_events_by_admin(admin_id):
        """Get all events created by an admin"""
        conn = get_db_connection()
        events = conn.execute(
            '''SELECT e.*, 
                      COUNT(DISTINCT en.student_id) as notification_count
               FROM exam_events e
               LEFT JOIN event_notifications en ON e.id = en.event_id
               WHERE e.created_by = ? AND e.is_active = 1
               GROUP BY e.id
               ORDER BY e.event_date ASC, e.start_time ASC''',
            (admin_id,)
        ).fetchall()
        conn.close()
        return events
    
    @staticmethod
    def get_events_for_student(student_id):
        """Get events visible to a specific student"""
        conn = get_db_connection()
        
        # Get student details
        student = conn.execute(
            'SELECT department, semester FROM students WHERE id = ?',
            (student_id,)
        ).fetchone()
        
        if not student:
            conn.close()
            return []
        
        # Get events based on target audience
        events = conn.execute('''
            SELECT e.*, a.name as created_by_name,
                   CASE WHEN en.id IS NOT NULL THEN 1 ELSE 0 END as is_notified
            FROM exam_events e
            JOIN admin a ON e.created_by = a.id
            LEFT JOIN event_notifications en ON e.id = en.event_id AND en.student_id = ?
            WHERE e.is_active = 1 AND (
                e.target_audience = 'all' OR
                (e.target_audience = 'department' AND e.department = ?) OR
                (e.target_audience = 'semester' AND e.semester = ?) OR
                (e.target_audience = 'class' AND e.department = ? AND e.semester = ?)
            )
            ORDER BY e.event_date ASC, e.start_time ASC
        ''', (student_id, student['department'], student['semester'], 
              student['department'], student['semester'])).fetchall()
        
        conn.close()
        return events
    
    @staticmethod
    def get_calendar_events(student_id=None, start_date=None, end_date=None):
        """Get events for calendar display"""
        conn = get_db_connection()
        
        if student_id:
            # Get student-specific events
            student = conn.execute(
                'SELECT department, semester FROM students WHERE id = ?',
                (student_id,)
            ).fetchone()
            
            if not student:
                conn.close()
                return []
            
            query = '''
                SELECT e.id, e.title, e.description, e.event_date, 
                       e.start_time, e.end_time, e.event_type
                FROM exam_events e
                WHERE e.is_active = 1 AND (
                    e.target_audience = 'all' OR
                    (e.target_audience = 'department' AND e.department = ?) OR
                    (e.target_audience = 'semester' AND e.semester = ?) OR
                    (e.target_audience = 'class' AND e.department = ? AND e.semester = ?)
                )
            '''
            params = [student['department'], student['semester'], 
                     student['department'], student['semester']]
        else:
            # Get all events (admin view)
            query = '''
                SELECT e.id, e.title, e.description, e.event_date, 
                       e.start_time, e.end_time, e.event_type
                FROM exam_events e
                WHERE e.is_active = 1
            '''
            params = []
        
        # Add date range filter if provided
        if start_date and end_date:
            query += ' AND e.event_date BETWEEN ? AND ?'
            params.extend([start_date, end_date])
        
        query += ' ORDER BY e.event_date ASC, e.start_time ASC'
        
        events = conn.execute(query, params).fetchall()
        conn.close()
        
        # Convert to FullCalendar format
        calendar_events = []
        for event in events:
            calendar_events.append({
                'id': event['id'],
                'title': event['title'],
                'start': f"{event['event_date']}T{event['start_time']}",
                'end': f"{event['event_date']}T{event['end_time']}",
                'description': event['description'],
                'type': event['event_type'],
                'className': f'event-{event["event_type"]}'
            })
        
        return calendar_events
    
    @staticmethod
    def update_event(event_id, title=None, description=None, event_date=None,
                    start_time=None, end_time=None, event_type=None,
                    semester=None, department=None, target_audience=None):
        """Update an existing event"""
        try:
            conn = get_db_connection()
            
            # Build dynamic update query
            update_fields = []
            params = []
            
            if title is not None:
                update_fields.append('title = ?')
                params.append(title)
            if description is not None:
                update_fields.append('description = ?')
                params.append(description)
            if event_date is not None:
                update_fields.append('event_date = ?')
                params.append(event_date)
            if start_time is not None:
                update_fields.append('start_time = ?')
                params.append(start_time)
            if end_time is not None:
                update_fields.append('end_time = ?')
                params.append(end_time)
            if event_type is not None:
                update_fields.append('event_type = ?')
                params.append(event_type)
            if semester is not None:
                update_fields.append('semester = ?')
                params.append(semester)
            if department is not None:
                update_fields.append('department = ?')
                params.append(department)
            if target_audience is not None:
                update_fields.append('target_audience = ?')
                params.append(target_audience)
            
            if not update_fields:
                conn.close()
                return False
            
            update_fields.append('updated_at = CURRENT_TIMESTAMP')
            params.append(event_id)
            
            query = f'''
                UPDATE exam_events 
                SET {', '.join(update_fields)}
                WHERE id = ? AND is_active = 1
            '''
            
            conn.execute(query, params)
            conn.commit()
            conn.close()
            
            # Send update notifications
            EventService._send_event_notifications(event_id, 'updated')
            EventService._broadcast_event_update(event_id, 'updated')
            
            return True
        except Exception as e:
            print(f"Error updating event: {e}")
            return False
    
    @staticmethod
    def delete_event(event_id):
        """Soft delete an event"""
        try:
            conn = get_db_connection()
            conn.execute(
                'UPDATE exam_events SET is_active = 0, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
                (event_id,)
            )
            conn.commit()
            conn.close()
            
            # Send deletion notifications
            EventService._send_event_notifications(event_id, 'cancelled')
            EventService._broadcast_event_update(event_id, 'deleted')
            
            return True
        except Exception as e:
            print(f"Error deleting event: {e}")
            return False
    
    @staticmethod
    def get_upcoming_events(student_id, days_ahead=7):
        """Get upcoming events for a student"""
        conn = get_db_connection()
        
        student = conn.execute(
            'SELECT department, semester FROM students WHERE id = ?',
            (student_id,)
        ).fetchone()
        
        if not student:
            conn.close()
            return []
        
        events = conn.execute('''
            SELECT e.*, a.name as created_by_name
            FROM exam_events e
            JOIN admin a ON e.created_by = a.id
            WHERE e.is_active = 1 
            AND e.event_date >= date('now') 
            AND e.event_date <= date('now', '+' || ? || ' days')
            AND (
                e.target_audience = 'all' OR
                (e.target_audience = 'department' AND e.department = ?) OR
                (e.target_audience = 'semester' AND e.semester = ?) OR
                (e.target_audience = 'class' AND e.department = ? AND e.semester = ?)
            )
            ORDER BY e.event_date ASC, e.start_time ASC
        ''', (days_ahead, student['department'], student['semester'],
              student['department'], student['semester'])).fetchall()
        
        conn.close()
        return events
    
    @staticmethod
    def get_event_statistics():
        """Get event statistics for admin dashboard"""
        conn = get_db_connection()
        
        stats = {
            'total_events': 0,
            'upcoming_events': 0,
            'past_events': 0,
            'events_by_type': {},
            'notifications_sent': 0
        }
        
        # Total events
        stats['total_events'] = conn.execute(
            'SELECT COUNT(*) FROM exam_events WHERE is_active = 1'
        ).fetchone()[0]
        
        # Upcoming events
        stats['upcoming_events'] = conn.execute(
            'SELECT COUNT(*) FROM exam_events WHERE is_active = 1 AND event_date >= date("now")'
        ).fetchone()[0]
        
        # Past events
        stats['past_events'] = conn.execute(
            'SELECT COUNT(*) FROM exam_events WHERE is_active = 1 AND event_date < date("now")'
        ).fetchone()[0]
        
        # Events by type
        event_types = conn.execute('''
            SELECT event_type, COUNT(*) as count
            FROM exam_events 
            WHERE is_active = 1
            GROUP BY event_type
        ''').fetchall()
        
        for event_type in event_types:
            stats['events_by_type'][event_type['event_type']] = event_type['count']
        
        # Notifications sent
        stats['notifications_sent'] = conn.execute(
            'SELECT COUNT(*) FROM event_notifications'
        ).fetchone()[0]
        
        conn.close()
        return stats
    
    @staticmethod
    def _send_event_notifications(event_id, action_type):
        """Send email notifications for event (async)"""
        try:
            conn = get_db_connection()
            
            # Get event details
            event = conn.execute(
                'SELECT * FROM exam_events WHERE id = ?',
                (event_id,)
            ).fetchone()
            
            if not event:
                conn.close()
                return
            
            # Get target students
            students = EventService._get_target_students(
                event['target_audience'], 
                event['semester'], 
                event['department']
            )
            
            # Send emails
            for student in students:
                try:
                    EmailService.send_event_notification(
                        student['email'],
                        student['name'],
                        event,
                        action_type
                    )
                    
                    # Log notification
                    conn.execute('''
                        INSERT OR REPLACE INTO event_notifications
                        (event_id, student_id, notification_type)
                        VALUES (?, ?, ?)
                    ''', (event_id, student['id'], action_type))
                    
                except Exception as e:
                    print(f"Failed to send email to {student['email']}: {e}")
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"Error sending event notifications: {e}")
    
    @staticmethod
    def _get_target_students(target_audience, semester, department):
        """Get students based on target audience"""
        conn = get_db_connection()
        
        if target_audience == 'all':
            students = conn.execute(
                'SELECT id, name, email FROM students'
            ).fetchall()
        elif target_audience == 'department':
            students = conn.execute(
                'SELECT id, name, email FROM students WHERE department = ?',
                (department,)
            ).fetchall()
        elif target_audience == 'semester':
            students = conn.execute(
                'SELECT id, name, email FROM students WHERE semester = ?',
                (semester,)
            ).fetchall()
        elif target_audience == 'class':
            students = conn.execute(
                'SELECT id, name, email FROM students WHERE department = ? AND semester = ?',
                (department, semester)
            ).fetchall()
        else:
            students = []
        
        conn.close()
        return students
    
    @staticmethod
    def _broadcast_event_update(event_id, action_type):
        """Broadcast real-time event update via WebSocket"""
        try:
            event = EventService.get_event_by_id(event_id)
            if event:
                # Get target students
                students = EventService._get_target_students(
                    event['target_audience'],
                    event['semester'],
                    event['department']
                )
                
                # Broadcast to each student
                for student in students:
                    WebSocketHandler.broadcast_event_update(
                        student_id=student['id'],
                        event_data={
                            'id': event['id'],
                            'title': event['title'],
                            'date': event['event_date'],
                            'start_time': event['start_time'],
                            'end_time': event['end_time'],
                            'action': action_type
                        }
                    )
        except Exception as e:
            print(f"Error broadcasting event update: {e}")