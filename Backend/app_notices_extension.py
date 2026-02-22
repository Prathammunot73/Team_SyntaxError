"""
Notice & Timetable Management Routes Extension
Add these routes to app_notifications.py
"""

from flask import request, jsonify, send_file
from werkzeug.utils import secure_filename
from utils.notice_service import NoticeService, NOTICE_TYPES
from utils.file_handler import FileHandler
from utils.notification_service import NotificationService, NOTIFICATION_TYPES
from utils.websocket_handler import WebSocketHandler
import os

# ============================================================================
# NOTICE MANAGEMENT ROUTES (Add to app_notifications.py)
# ============================================================================

@app.route('/admin/upload-notice', methods=['GET', 'POST'])
@admin_login_required
def admin_upload_notice():
    """Admin page to upload notices and timetables"""
    if request.method == 'POST':
        try:
            # Get form data
            title = request.form.get('title')
            description = request.form.get('description', '')
            notice_type = request.form.get('notice_type')
            target_role = request.form.get('target_role', 'all')
            department = request.form.get('department')
            semester = request.form.get('semester')
            publish_at = request.form.get('publish_at')
            
            # Validate required fields
            if not all([title, notice_type]):
                flash('Title and notice type are required', 'error')
                return redirect(url_for('admin_upload_notice'))
            
            # Get uploaded file
            if 'pdf_file' not in request.files:
                flash('No file uploaded', 'error')
                return redirect(url_for('admin_upload_notice'))
            
            file = request.files['pdf_file']
            
            # Save file
            success, result, file_size = FileHandler.save_file(file, notice_type)
            
            if not success:
                flash(f'File upload failed: {result}', 'error')
                return redirect(url_for('admin_upload_notice'))
            
            file_path = result
            file_name = file.filename
            
            # Create notice in database
            notice_id = NoticeService.create_notice(
                title=title,
                description=description,
                file_url=file_path,
                file_name=file_name,
                file_size=file_size,
                notice_type=notice_type,
                target_role=target_role,
                department=department if target_role in ['department', 'class'] else None,
                semester=semester if target_role in ['semester', 'class'] else None,
                uploaded_by=session['user_id'],
                publish_at=publish_at if publish_at else None
            )
            
            if not notice_id:
                flash('Error creating notice in database', 'error')
                FileHandler.delete_file(file_path)
                return redirect(url_for('admin_upload_notice'))
            
            # Get targeted students
            targeted_students = NoticeService.get_targeted_students(
                target_role, department, semester
            )
            
            # Send notifications to targeted students
            notification_title = f"New {notice_type.title()}: {title}"
            notification_message = f"A new {notice_type} has been uploaded. Click to view."
            
            for student_id in targeted_students:
                # Create notification
                notif_id = NotificationService.create_notification(
                    student_id=student_id,
                    title=notification_title,
                    message=notification_message,
                    notification_type=NOTIFICATION_TYPES['NOTICE'],
                    related_id=notice_id
                )
                
                # Broadcast via WebSocket
                if notif_id:
                    notification_data = {
                        'id': notif_id,
                        'title': notification_title,
                        'message': notification_message,
                        'type': 'notice',
                        'related_id': notice_id,
                        'is_read': 0,
                        'created_at': 'Just now'
                    }
                    WebSocketHandler.broadcast_notification(socketio, student_id, notification_data)
            
            flash(f'Notice uploaded successfully! Notifications sent to {len(targeted_students)} students.', 'success')
            return redirect(url_for('admin_manage_notices'))
            
        except Exception as e:
            logger.error(f"Error uploading notice: {e}")
            flash(f'Error uploading notice: {str(e)}', 'error')
            return redirect(url_for('admin_upload_notice'))
    
    return render_template('admin_upload_notice.html')

@app.route('/admin/manage-notices')
@admin_login_required
def admin_manage_notices():
    """Admin page to manage all notices"""
    notice_type = request.args.get('type')
    notices = NoticeService.get_all_notices(notice_type=notice_type)
    
    return render_template('admin_manage_notices.html', notices=notices)

@app.route('/admin/notice/<int:notice_id>/edit', methods=['GET', 'POST'])
@admin_login_required
def admin_edit_notice(notice_id):
    """Edit notice details"""
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        target_role = request.form.get('target_role')
        department = request.form.get('department')
        semester = request.form.get('semester')
        
        success = NoticeService.update_notice(
            notice_id=notice_id,
            title=title,
            description=description,
            target_role=target_role,
            department=department,
            semester=semester
        )
        
        if success:
            flash('Notice updated successfully!', 'success')
        else:
            flash('Error updating notice', 'error')
        
        return redirect(url_for('admin_manage_notices'))
    
    notice = NoticeService.get_notice_by_id(notice_id)
    if not notice:
        flash('Notice not found', 'error')
        return redirect(url_for('admin_manage_notices'))
    
    return render_template('admin_edit_notice.html', notice=notice)

@app.route('/admin/notice/<int:notice_id>/delete', methods=['POST'])
@admin_login_required
def admin_delete_notice(notice_id):
    """Delete a notice"""
    success = NoticeService.delete_notice(notice_id)
    
    if success:
        flash('Notice deleted successfully!', 'success')
    else:
        flash('Error deleting notice', 'error')
    
    return redirect(url_for('admin_manage_notices'))

@app.route('/student/notices')
@student_login_required
def student_notices():
    """Student page to view all notices"""
    notices = NoticeService.get_notices_for_student(
        student_id=session['user_id'],
        notice_type=None
    )
    
    unread_count = NoticeService.get_unread_count(session['user_id'])
    
    return render_template('student_notices.html', 
                         notices=notices, 
                         unread_count=unread_count)

@app.route('/student/timetable')
@student_login_required
def student_timetable():
    """Student page to view timetable"""
    # Get current timetable
    timetables = NoticeService.get_notices_for_student(
        student_id=session['user_id'],
        notice_type=NOTICE_TYPES['TIMETABLE'],
        limit=10
    )
    
    current_timetable = timetables[0] if timetables else None
    previous_timetables = timetables[1:] if len(timetables) > 1 else []
    
    return render_template('student_timetable.html',
                         timetable=current_timetable,
                         previous_timetables=previous_timetables)

@app.route('/download-notice/<int:notice_id>')
@student_login_required
def download_notice(notice_id):
    """Download a notice PDF"""
    notice = NoticeService.get_notice_by_id(notice_id)
    
    if not notice:
        flash('Notice not found', 'error')
        return redirect(url_for('student_notices'))
    
    # Check if student has access
    student_id = session['user_id']
    notices = NoticeService.get_notices_for_student(student_id)
    notice_ids = [n['id'] for n in notices]
    
    if notice_id not in notice_ids:
        flash('Access denied', 'error')
        return redirect(url_for('student_notices'))
    
    # Increment download count
    NoticeService.increment_download_count(notice_id)
    
    # Mark as read
    NoticeService.mark_notice_read(notice_id, student_id)
    
    # Send file
    file_path = notice['file_url']
    if os.path.exists(file_path):
        return send_file(file_path, 
                        as_attachment=True,
                        download_name=notice['file_name'])
    else:
        flash('File not found', 'error')
        return redirect(url_for('student_notices'))

# ============================================================================
# NOTICE API ENDPOINTS
# ============================================================================

@app.route('/api/notices/<int:notice_id>/read', methods=['POST'])
@student_login_required
def api_mark_notice_read(notice_id):
    """Mark a notice as read"""
    success = NoticeService.mark_notice_read(notice_id, session['user_id'])
    return jsonify({'success': success})

@app.route('/api/notices/unread-count')
@student_login_required
def api_notice_unread_count():
    """Get unread notice count"""
    count = NoticeService.get_unread_count(session['user_id'])
    return jsonify({'count': count})

@app.route('/api/notices/stats')
@admin_login_required
def api_notice_stats():
    """Get notice statistics for admin"""
    stats = NoticeService.get_notice_statistics()
    return jsonify(stats)
