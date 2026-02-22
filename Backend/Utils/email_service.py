"""
Email Service for Event Notifications
Handles automatic email notifications for exam events
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import threading


class EmailService:
    """Service for sending email notifications"""
    
    # Email configuration (update with your SMTP settings)
    SMTP_SERVER = 'smtp.gmail.com'
    SMTP_PORT = 587
    EMAIL_ADDRESS = 'your-college-email@gmail.com'  # Update this
    EMAIL_PASSWORD = 'your-app-password'  # Update this
    
    @staticmethod
    def send_event_notification(student_email, student_name, event, action_type):
        """
        Send event notification email to student
        
        Args:
            student_email (str): Student's email address
            student_name (str): Student's name
            event (dict): Event details
            action_type (str): 'created', 'updated', or 'cancelled'
        """
        try:
            # Create email content
            subject, body = EmailService._create_email_content(
                student_name, event, action_type
            )
            
            # Send email in background thread
            thread = threading.Thread(
                target=EmailService._send_email_async,
                args=(student_email, subject, body)
            )
            thread.daemon = True
            thread.start()
            
        except Exception as e:
            print(f"Error preparing email notification: {e}")
    
    @staticmethod
    def _create_email_content(student_name, event, action_type):
        """Create email subject and body"""
        
        # Format date and time
        event_date = datetime.strptime(event['event_date'], '%Y-%m-%d').strftime('%d %b %Y')
        start_time = datetime.strptime(event['start_time'], '%H:%M:%S').strftime('%I:%M %p')
        end_time = datetime.strptime(event['end_time'], '%H:%M:%S').strftime('%I:%M %p')
        
        # Create subject based on action
        if action_type == 'created':
            subject = f"New {event['event_type'].title()} Scheduled: {event['title']}"
        elif action_type == 'updated':
            subject = f"{event['event_type'].title()} Updated: {event['title']}"
        elif action_type == 'cancelled':
            subject = f"{event['event_type'].title()} Cancelled: {event['title']}"
        else:
            subject = f"Event Notification: {event['title']}"
        
        # Create HTML body
        if action_type == 'created':
            body = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: #007bff; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
                    .content {{ background: #f8f9fa; padding: 30px; border-radius: 0 0 8px 8px; }}
                    .event-details {{ background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #007bff; }}
                    .detail-row {{ margin: 10px 0; }}
                    .label {{ font-weight: bold; color: #666; }}
                    .value {{ color: #333; }}
                    .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 0.9em; }}
                    .btn {{ display: inline-block; padding: 12px 24px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>📅 New {event['event_type'].title()} Scheduled</h1>
                    </div>
                    <div class="content">
                        <p>Dear <strong>{student_name}</strong>,</p>
                        
                        <p>A new {event['event_type']} has been scheduled. Please check your dashboard for complete details.</p>
                        
                        <div class="event-details">
                            <h3>📋 Event Details</h3>
                            <div class="detail-row">
                                <span class="label">Title:</span>
                                <span class="value">{event['title']}</span>
                            </div>
                            <div class="detail-row">
                                <span class="label">Date:</span>
                                <span class="value">{event_date}</span>
                            </div>
                            <div class="detail-row">
                                <span class="label">Time:</span>
                                <span class="value">{start_time} - {end_time}</span>
                            </div>
                            <div class="detail-row">
                                <span class="label">Type:</span>
                                <span class="value">{event['event_type'].title()}</span>
                            </div>
                            {f'<div class="detail-row"><span class="label">Semester:</span><span class="value">{event["semester"]}</span></div>' if event.get('semester') else ''}
                            {f'<div class="detail-row"><span class="label">Department:</span><span class="value">{event["department"]}</span></div>' if event.get('department') else ''}
                            {f'<div class="detail-row"><span class="label">Description:</span><span class="value">{event["description"]}</span></div>' if event.get('description') else ''}
                        </div>
                        
                        <p><strong>⚠️ Important:</strong> Please mark this date in your calendar and prepare accordingly.</p>
                        
                        <div class="footer">
                            <p>This is an automated notification from the College Examination System.</p>
                            <p>Please do not reply to this email.</p>
                        </div>
                    </div>
                </div>
            </body>
            </html>
            """
        
        elif action_type == 'updated':
            body = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: #ffc107; color: #333; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
                    .content {{ background: #f8f9fa; padding: 30px; border-radius: 0 0 8px 8px; }}
                    .event-details {{ background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #ffc107; }}
                    .detail-row {{ margin: 10px 0; }}
                    .label {{ font-weight: bold; color: #666; }}
                    .value {{ color: #333; }}
                    .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 0.9em; }}
                    .alert {{ background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; margin: 20px 0; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🔄 {event['event_type'].title()} Updated</h1>
                    </div>
                    <div class="content">
                        <p>Dear <strong>{student_name}</strong>,</p>
                        
                        <div class="alert">
                            <strong>⚠️ Important Update:</strong> The details for "{event['title']}" have been modified.
                        </div>
                        
                        <div class="event-details">
                            <h3>📋 Updated Event Details</h3>
                            <div class="detail-row">
                                <span class="label">Title:</span>
                                <span class="value">{event['title']}</span>
                            </div>
                            <div class="detail-row">
                                <span class="label">Date:</span>
                                <span class="value">{event_date}</span>
                            </div>
                            <div class="detail-row">
                                <span class="label">Time:</span>
                                <span class="value">{start_time} - {end_time}</span>
                            </div>
                            <div class="detail-row">
                                <span class="label">Type:</span>
                                <span class="value">{event['event_type'].title()}</span>
                            </div>
                            {f'<div class="detail-row"><span class="label">Description:</span><span class="value">{event["description"]}</span></div>' if event.get('description') else ''}
                        </div>
                        
                        <p><strong>📅 Action Required:</strong> Please update your calendar with the new details.</p>
                        
                        <div class="footer">
                            <p>This is an automated notification from the College Examination System.</p>
                            <p>Please do not reply to this email.</p>
                        </div>
                    </div>
                </div>
            </body>
            </html>
            """
        
        elif action_type == 'cancelled':
            body = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: #dc3545; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
                    .content {{ background: #f8f9fa; padding: 30px; border-radius: 0 0 8px 8px; }}
                    .event-details {{ background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #dc3545; }}
                    .detail-row {{ margin: 10px 0; }}
                    .label {{ font-weight: bold; color: #666; }}
                    .value {{ color: #333; }}
                    .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 0.9em; }}
                    .alert {{ background: #f8d7da; border: 1px solid #f5c6cb; padding: 15px; border-radius: 5px; margin: 20px 0; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>❌ {event['event_type'].title()} Cancelled</h1>
                    </div>
                    <div class="content">
                        <p>Dear <strong>{student_name}</strong>,</p>
                        
                        <div class="alert">
                            <strong>🚨 Important Notice:</strong> The following event has been cancelled.
                        </div>
                        
                        <div class="event-details">
                            <h3>📋 Cancelled Event Details</h3>
                            <div class="detail-row">
                                <span class="label">Title:</span>
                                <span class="value">{event['title']}</span>
                            </div>
                            <div class="detail-row">
                                <span class="label">Original Date:</span>
                                <span class="value">{event_date}</span>
                            </div>
                            <div class="detail-row">
                                <span class="label">Original Time:</span>
                                <span class="value">{start_time} - {end_time}</span>
                            </div>
                        </div>
                        
                        <p><strong>📅 Action Required:</strong> Please remove this event from your calendar. Further updates will be communicated separately.</p>
                        
                        <div class="footer">
                            <p>This is an automated notification from the College Examination System.</p>
                            <p>Please do not reply to this email.</p>
                        </div>
                    </div>
                </div>
            </body>
            </html>
            """
        
        return subject, body
    
    @staticmethod
    def _send_email_async(to_email, subject, body):
        """Send email asynchronously"""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = EmailService.EMAIL_ADDRESS
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add HTML body
            html_part = MIMEText(body, 'html')
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(EmailService.SMTP_SERVER, EmailService.SMTP_PORT) as server:
                server.starttls()
                server.login(EmailService.EMAIL_ADDRESS, EmailService.EMAIL_PASSWORD)
                server.send_message(msg)
            
            print(f"Email sent successfully to {to_email}")
            
        except Exception as e:
            print(f"Failed to send email to {to_email}: {e}")
    
    @staticmethod
    def test_email_configuration():
        """Test email configuration"""
        try:
            with smtplib.SMTP(EmailService.SMTP_SERVER, EmailService.SMTP_PORT) as server:
                server.starttls()
                server.login(EmailService.EMAIL_ADDRESS, EmailService.EMAIL_PASSWORD)
            print("✓ Email configuration is working")
            return True
        except Exception as e:
            print(f"✗ Email configuration error: {e}")
            return False