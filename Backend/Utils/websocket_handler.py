"""
WebSocket Handler for Real-time Notifications
Manages WebSocket connections and broadcasts notifications
"""

from flask_socketio import emit, join_room, leave_room, disconnect
from flask import request, session
import logging

logger = logging.getLogger(__name__)

# Store active connections: {student_id: [session_ids]}
active_connections = {}

class WebSocketHandler:
    """Handler for WebSocket events"""
    
    @staticmethod
    def handle_connect(socketio):
        """Handle client connection"""
        try:
            # Get user info from session
            user_id = session.get('user_id')
            user_type = session.get('user_type')
            
            if not user_id or user_type != 'student':
                logger.warning(f"Unauthorized WebSocket connection attempt")
                disconnect()
                return False
            
            # Join user-specific room
            room = f"student_{user_id}"
            join_room(room)
            
            # Track connection
            if user_id not in active_connections:
                active_connections[user_id] = []
            active_connections[user_id].append(request.sid)
            
            logger.info(f"Student {user_id} connected via WebSocket (SID: {request.sid})")
            
            # Send connection confirmation
            emit('connected', {
                'status': 'success',
                'message': 'Connected to notification service',
                'user_id': user_id
            })
            
            return True
        except Exception as e:
            logger.error(f"Error handling WebSocket connection: {e}")
            return False
    
    @staticmethod
    def handle_disconnect():
        """Handle client disconnection"""
        try:
            user_id = session.get('user_id')
            
            if user_id and user_id in active_connections:
                if request.sid in active_connections[user_id]:
                    active_connections[user_id].remove(request.sid)
                
                # Clean up if no more connections
                if not active_connections[user_id]:
                    del active_connections[user_id]
            
            logger.info(f"Client disconnected (SID: {request.sid})")
        except Exception as e:
            logger.error(f"Error handling WebSocket disconnection: {e}")
    
    @staticmethod
    def handle_mark_read(data):
        """Handle mark notification as read"""
        try:
            from utils.notification_service import NotificationService
            
            notification_id = data.get('notification_id')
            user_id = session.get('user_id')
            
            if not notification_id or not user_id:
                emit('error', {'message': 'Invalid request'})
                return
            
            success = NotificationService.mark_as_read(notification_id, user_id)
            
            if success:
                emit('notification_read', {
                    'notification_id': notification_id,
                    'status': 'success'
                })
            else:
                emit('error', {'message': 'Failed to mark notification as read'})
        except Exception as e:
            logger.error(f"Error marking notification as read: {e}")
            emit('error', {'message': 'Server error'})
    
    @staticmethod
    def handle_mark_all_read():
        """Handle mark all notifications as read"""
        try:
            from utils.notification_service import NotificationService
            
            user_id = session.get('user_id')
            
            if not user_id:
                emit('error', {'message': 'Unauthorized'})
                return
            
            success = NotificationService.mark_all_as_read(user_id)
            
            if success:
                emit('all_notifications_read', {'status': 'success'})
            else:
                emit('error', {'message': 'Failed to mark all notifications as read'})
        except Exception as e:
            logger.error(f"Error marking all notifications as read: {e}")
            emit('error', {'message': 'Server error'})
    
    @staticmethod
    def handle_get_unread_count():
        """Handle get unread notification count"""
        try:
            from utils.notification_service import NotificationService
            
            user_id = session.get('user_id')
            
            if not user_id:
                emit('error', {'message': 'Unauthorized'})
                return
            
            count = NotificationService.get_unread_count(user_id)
            
            emit('unread_count', {'count': count})
        except Exception as e:
            logger.error(f"Error getting unread count: {e}")
            emit('error', {'message': 'Server error'})
    
    @staticmethod
    def broadcast_notification(socketio, student_id, notification_data):
        """
        Broadcast notification to a specific student
        
        Args:
            socketio: SocketIO instance
            student_id: ID of student to notify
            notification_data: Notification data dict
        """
        try:
            room = f"student_{student_id}"
            
            # Check if student is online
            is_online = student_id in active_connections and len(active_connections[student_id]) > 0
            
            if is_online:
                socketio.emit('new_notification', notification_data, room=room)
                logger.info(f"Notification broadcast to student {student_id} (online)")
            else:
                logger.info(f"Notification stored for student {student_id} (offline)")
            
            return is_online
        except Exception as e:
            logger.error(f"Error broadcasting notification: {e}")
            return False
    
    @staticmethod
    def broadcast_to_all_students(socketio, notification_data):
        """
        Broadcast notification to all connected students
        
        Args:
            socketio: SocketIO instance
            notification_data: Notification data dict
        """
        try:
            count = 0
            for student_id in active_connections.keys():
                room = f"student_{student_id}"
                socketio.emit('new_notification', notification_data, room=room)
                count += 1
            
            logger.info(f"Notification broadcast to {count} online students")
            return count
        except Exception as e:
            logger.error(f"Error broadcasting to all students: {e}")
            return 0
    
    @staticmethod
    def is_student_online(student_id):
        """Check if a student is currently online"""
        return student_id in active_connections and len(active_connections[student_id]) > 0
    
    @staticmethod
    def get_online_students():
        """Get list of currently online student IDs"""
        return list(active_connections.keys())
    
    @staticmethod
    def get_connection_count():
        """Get total number of active connections"""
        return sum(len(sessions) for sessions in active_connections.values())
    
    @staticmethod
    def broadcast_event_update(student_id, event_data):
        """Broadcast event update to specific student"""
        try:
            from app import socketio  # Import here to avoid circular import
            
            room = f"student_{student_id}"
            
            # Check if student is online
            is_online = student_id in active_connections and len(active_connections[student_id]) > 0
            
            if is_online:
                socketio.emit('event_update', event_data, room=room)
                logger.info(f"Event update sent to student {student_id}")
            
            return is_online
        except Exception as e:
            logger.error(f"Error broadcasting event update: {e}")
            return False
    
    @staticmethod
    def broadcast_calendar_refresh(student_id):
        """Broadcast calendar refresh signal to student"""
        try:
            from app import socketio  # Import here to avoid circular import
            
            room = f"student_{student_id}"
            
            # Check if student is online
            is_online = student_id in active_connections and len(active_connections[student_id]) > 0
            
            if is_online:
                socketio.emit('calendar_refresh', {'refresh': True}, room=room)
                logger.info(f"Calendar refresh sent to student {student_id}")
            
            return is_online
        except Exception as e:
            logger.error(f"Error broadcasting calendar refresh: {e}")
            return False
