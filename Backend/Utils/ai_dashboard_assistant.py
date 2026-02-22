"""
AI Dashboard Assistant
Provides AI-powered insights and recommendations for faculty and admin dashboards
"""

import sqlite3
from datetime import datetime, timedelta
from collections import Counter
import re


def parse_deadline(deadline_str):
    """
    Parse deadline string in multiple formats
    
    Args:
        deadline_str: Deadline string in various formats
        
    Returns:
        datetime object or None if parsing fails
    """
    if not deadline_str:
        return None
    
    # Try ISO format first (2026-02-22T02:10)
    try:
        return datetime.fromisoformat(deadline_str.replace('T', ' '))
    except:
        pass
    
    # Try SQL datetime format (2026-02-22 02:10:00)
    try:
        return datetime.strptime(deadline_str, '%Y-%m-%d %H:%M:%S')
    except:
        pass
    
    # Try without seconds (2026-02-22 02:10)
    try:
        return datetime.strptime(deadline_str, '%Y-%m-%d %H:%M')
    except:
        pass
    
    return None


class AIDashboardAssistant:
    """AI-powered dashboard insights and recommendations"""
    
    @staticmethod
    def get_student_insights(student_id, db_connection):
        """
        Generate AI-powered insights for student dashboard
        
        Args:
            student_id (int): Student ID
            db_connection: Database connection
            
        Returns:
            dict: Comprehensive insights and recommendations
        """
        insights = {
            'assignment_status': AIDashboardAssistant._analyze_student_assignments(student_id, db_connection),
            'performance_summary': AIDashboardAssistant._analyze_student_performance(student_id, db_connection),
            'upcoming_events': AIDashboardAssistant._get_student_upcoming_events(student_id, db_connection),
            'recommendations': AIDashboardAssistant._generate_student_recommendations(student_id, db_connection),
            'alerts': AIDashboardAssistant._generate_student_alerts(student_id, db_connection)
        }
        
        return insights
    
    @staticmethod
    def get_faculty_insights(faculty_id, db_connection):
        """
        Generate AI-powered insights for faculty dashboard
        
        Args:
            faculty_id (int): Faculty ID
            db_connection: Database connection
            
        Returns:
            dict: Comprehensive insights and recommendations
        """
        insights = {
            'complaint_analysis': AIDashboardAssistant._analyze_complaints(faculty_id, db_connection),
            'student_performance': AIDashboardAssistant._analyze_student_performance(faculty_id, db_connection),
            'assignment_insights': AIDashboardAssistant._analyze_assignments(faculty_id, db_connection),
            'recommendations': AIDashboardAssistant._generate_faculty_recommendations(faculty_id, db_connection),
            'alerts': AIDashboardAssistant._generate_faculty_alerts(faculty_id, db_connection),
            'trends': AIDashboardAssistant._analyze_trends(faculty_id, db_connection)
        }
        
        return insights
    
    @staticmethod
    def get_admin_insights(db_connection):
        """
        Generate AI-powered insights for admin dashboard
        
        Args:
            db_connection: Database connection
            
        Returns:
            dict: System-wide insights and recommendations
        """
        insights = {
            'system_health': AIDashboardAssistant._analyze_system_health(db_connection),
            'user_engagement': AIDashboardAssistant._analyze_user_engagement(db_connection),
            'event_analytics': AIDashboardAssistant._analyze_event_effectiveness(db_connection),
            'assignment_analytics': AIDashboardAssistant._analyze_assignment_system(db_connection),
            'recommendations': AIDashboardAssistant._generate_admin_recommendations(db_connection),
            'alerts': AIDashboardAssistant._generate_admin_alerts(db_connection),
            'predictions': AIDashboardAssistant._generate_predictions(db_connection)
        }
        
        return insights
    
    # ==================== FACULTY INSIGHTS ====================
    
    @staticmethod
    def _analyze_complaints(faculty_id, conn):
        """Analyze complaint patterns for faculty"""
        try:
            # Get faculty subject
            faculty = conn.execute(
                'SELECT subject FROM faculty WHERE id = ?',
                (faculty_id,)
            ).fetchone()
            
            if not faculty:
                return None
            
            subject = faculty['subject']
            
            # Get complaints for this subject
            complaints = conn.execute('''
                SELECT status, ai_summary, extracted_question, created_at
                FROM complaints
                WHERE subject = ?
                ORDER BY created_at DESC
                LIMIT 50
            ''', (subject,)).fetchall()
            
            if not complaints:
                return {
                    'total': 0,
                    'message': 'No complaints to analyze',
                    'status': 'good'
                }
            
            # Analyze complaint patterns
            total = len(complaints)
            pending = sum(1 for c in complaints if c['status'] == 'pending')
            approved = sum(1 for c in complaints if c['status'] == 'approved')
            rejected = sum(1 for c in complaints if c['status'] == 'rejected')
            
            # Extract question patterns
            questions = [c['extracted_question'] for c in complaints if c['extracted_question'] != 'Unknown']
            question_freq = Counter(questions)
            most_common_questions = question_freq.most_common(3)
            
            # Calculate approval rate
            total_reviewed = approved + rejected
            approval_rate = (approved / total_reviewed * 100) if total_reviewed > 0 else 0
            
            # Generate insights
            insight_message = ""
            status = "good"
            
            if pending > 5:
                insight_message = f"⚠️ {pending} complaints pending review. Prompt action recommended."
                status = "warning"
            elif pending > 0:
                insight_message = f"📋 {pending} complaints awaiting your review."
                status = "info"
            else:
                insight_message = "✅ All complaints reviewed. Great job!"
                status = "good"
            
            # Identify problem areas
            problem_areas = []
            if most_common_questions:
                for q, count in most_common_questions:
                    if count >= 3:
                        problem_areas.append(f"{q} ({count} complaints)")
            
            return {
                'total': total,
                'pending': pending,
                'approved': approved,
                'rejected': rejected,
                'approval_rate': round(approval_rate, 1),
                'message': insight_message,
                'status': status,
                'problem_areas': problem_areas,
                'most_common_questions': most_common_questions
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def _analyze_student_performance(faculty_id, conn):
        """Analyze student performance patterns"""
        try:
            # Get faculty subject
            faculty = conn.execute(
                'SELECT subject FROM faculty WHERE id = ?',
                (faculty_id,)
            ).fetchone()
            
            if not faculty:
                return None
            
            subject = faculty['subject']
            
            # Get marks data
            marks = conn.execute('''
                SELECT marks, total_marks
                FROM internal_marks
                WHERE subject = ?
            ''', (subject,)).fetchall()
            
            if not marks:
                return {
                    'message': 'No marks data available',
                    'status': 'info'
                }
            
            # Calculate statistics
            percentages = [(m['marks'] / m['total_marks'] * 100) for m in marks if m['total_marks'] > 0]
            
            if not percentages:
                return {
                    'message': 'No valid marks data',
                    'status': 'info'
                }
            
            avg_percentage = sum(percentages) / len(percentages)
            
            # Categorize performance
            excellent = sum(1 for p in percentages if p >= 80)
            good = sum(1 for p in percentages if 60 <= p < 80)
            average = sum(1 for p in percentages if 40 <= p < 60)
            poor = sum(1 for p in percentages if p < 40)
            
            # Generate insights
            if avg_percentage >= 70:
                message = f"📈 Excellent class performance! Average: {avg_percentage:.1f}%"
                status = "excellent"
            elif avg_percentage >= 60:
                message = f"✅ Good class performance. Average: {avg_percentage:.1f}%"
                status = "good"
            elif avg_percentage >= 50:
                message = f"📊 Average class performance. Average: {avg_percentage:.1f}%"
                status = "average"
            else:
                message = f"⚠️ Class needs attention. Average: {avg_percentage:.1f}%"
                status = "warning"
            
            return {
                'average': round(avg_percentage, 1),
                'total_students': len(percentages),
                'excellent': excellent,
                'good': good,
                'average': average,
                'poor': poor,
                'message': message,
                'status': status
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def _analyze_assignments(faculty_id, conn):
        """Analyze assignment submission patterns"""
        try:
            # Get assignments created by faculty
            assignments = conn.execute('''
                SELECT a.id, a.title, a.deadline, a.bonus_strategy,
                       COUNT(s.id) as submission_count
                FROM assignments a
                LEFT JOIN submissions s ON a.id = s.assignment_id
                WHERE a.created_by = ?
                GROUP BY a.id
                ORDER BY a.deadline DESC
                LIMIT 10
            ''', (faculty_id,)).fetchall()
            
            if not assignments:
                return {
                    'message': 'No assignments created yet',
                    'status': 'info'
                }
            
            total_assignments = len(assignments)
            total_submissions = sum(a['submission_count'] for a in assignments)
            
            # Analyze submission rates
            active_assignments = [a for a in assignments if datetime.strptime(a['deadline'], '%Y-%m-%d %H:%M:%S') > datetime.now()]
            overdue_assignments = [a for a in assignments if datetime.strptime(a['deadline'], '%Y-%m-%d %H:%M:%S') <= datetime.now()]
            
            # Generate insights
            if active_assignments:
                message = f"📝 {len(active_assignments)} active assignments. Monitor submissions closely."
                status = "active"
            elif overdue_assignments:
                message = f"✅ All assignments completed. {total_submissions} total submissions received."
                status = "completed"
            else:
                message = "Create assignments to engage students."
                status = "info"
            
            return {
                'total_assignments': total_assignments,
                'active': len(active_assignments),
                'completed': len(overdue_assignments),
                'total_submissions': total_submissions,
                'message': message,
                'status': status
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def _generate_faculty_recommendations(faculty_id, conn):
        """Generate AI recommendations for faculty"""
        recommendations = []
        
        try:
            # Check pending complaints
            faculty = conn.execute('SELECT subject FROM faculty WHERE id = ?', (faculty_id,)).fetchone()
            if faculty:
                pending = conn.execute(
                    'SELECT COUNT(*) FROM complaints WHERE subject = ? AND status = "pending"',
                    (faculty['subject'],)
                ).fetchone()[0]
                
                if pending > 5:
                    recommendations.append({
                        'priority': 'high',
                        'icon': '⚠️',
                        'title': 'Review Pending Complaints',
                        'message': f'{pending} complaints need your attention. Timely review improves student satisfaction.',
                        'action': 'Review Complaints',
                        'link': '/faculty/dashboard'
                    })
                elif pending > 0:
                    recommendations.append({
                        'priority': 'medium',
                        'icon': '📋',
                        'title': 'Pending Reviews',
                        'message': f'{pending} complaints awaiting review.',
                        'action': 'View Complaints',
                        'link': '/faculty/dashboard'
                    })
            
            # Check for ungraded submissions
            ungraded = conn.execute('''
                SELECT COUNT(*) FROM submissions s
                JOIN assignments a ON s.assignment_id = a.id
                WHERE a.created_by = ? AND s.is_verified = 0
            ''', (faculty_id,)).fetchone()[0]
            
            if ungraded > 10:
                recommendations.append({
                    'priority': 'high',
                    'icon': '📝',
                    'title': 'Verify Submissions',
                    'message': f'{ungraded} submissions awaiting verification. Students are waiting for feedback.',
                    'action': 'Verify Now',
                    'link': '/faculty/assignments'
                })
            elif ungraded > 0:
                recommendations.append({
                    'priority': 'medium',
                    'icon': '✍️',
                    'title': 'Pending Verification',
                    'message': f'{ungraded} submissions need verification.',
                    'action': 'View Submissions',
                    'link': '/faculty/assignments'
                })
            
            # Check if no assignments created recently
            recent_assignments = conn.execute('''
                SELECT COUNT(*) FROM assignments
                WHERE created_by = ? AND created_at > datetime('now', '-30 days')
            ''', (faculty_id,)).fetchone()[0]
            
            if recent_assignments == 0:
                recommendations.append({
                    'priority': 'low',
                    'icon': '💡',
                    'title': 'Engage Students',
                    'message': 'No assignments created in the last 30 days. Consider creating new assignments.',
                    'action': 'Create Assignment',
                    'link': '/faculty/create_assignment'
                })
            
            # If no recommendations, add positive message
            if not recommendations:
                recommendations.append({
                    'priority': 'info',
                    'icon': '✅',
                    'title': 'All Caught Up!',
                    'message': 'Great work! No urgent actions required.',
                    'action': None,
                    'link': None
                })
            
        except Exception as e:
            recommendations.append({
                'priority': 'error',
                'icon': '❌',
                'title': 'Error',
                'message': f'Unable to generate recommendations: {str(e)}',
                'action': None,
                'link': None
            })
        
        return recommendations
    
    @staticmethod
    def _generate_faculty_alerts(faculty_id, conn):
        """Generate time-sensitive alerts for faculty"""
        alerts = []
        
        try:
            # Check for complaints older than 7 days
            old_complaints = conn.execute('''
                SELECT COUNT(*) FROM complaints c
                JOIN faculty f ON c.subject = f.subject
                WHERE f.id = ? AND c.status = 'pending' 
                AND c.created_at < datetime('now', '-7 days')
            ''', (faculty_id,)).fetchone()[0]
            
            if old_complaints > 0:
                alerts.append({
                    'type': 'warning',
                    'message': f'{old_complaints} complaint(s) pending for over 7 days',
                    'action': 'Review Now'
                })
            
            # Check for assignments with low submission rate
            low_submission = conn.execute('''
                SELECT a.title, COUNT(s.id) as submissions
                FROM assignments a
                LEFT JOIN submissions s ON a.id = s.assignment_id
                WHERE a.created_by = ? AND a.deadline > datetime('now')
                GROUP BY a.id
                HAVING submissions < 5
            ''', (faculty_id,)).fetchall()
            
            if low_submission:
                alerts.append({
                    'type': 'info',
                    'message': f'{len(low_submission)} assignment(s) have low submission rates',
                    'action': 'View Details'
                })
            
        except Exception as e:
            pass
        
        return alerts
    
    @staticmethod
    def _analyze_trends(faculty_id, conn):
        """Analyze trends over time"""
        try:
            # Complaint trend (last 30 days)
            faculty = conn.execute('SELECT subject FROM faculty WHERE id = ?', (faculty_id,)).fetchone()
            
            if not faculty:
                return None
            
            complaints_trend = conn.execute('''
                SELECT DATE(created_at) as date, COUNT(*) as count
                FROM complaints
                WHERE subject = ? AND created_at > datetime('now', '-30 days')
                GROUP BY DATE(created_at)
                ORDER BY date
            ''', (faculty['subject'],)).fetchall()
            
            # Calculate trend direction
            if len(complaints_trend) >= 2:
                recent_avg = sum(c['count'] for c in complaints_trend[-7:]) / min(7, len(complaints_trend[-7:]))
                older_avg = sum(c['count'] for c in complaints_trend[:-7]) / max(1, len(complaints_trend[:-7]))
                
                if recent_avg > older_avg * 1.2:
                    trend = "increasing"
                    message = "⬆️ Complaint volume increasing. Monitor closely."
                elif recent_avg < older_avg * 0.8:
                    trend = "decreasing"
                    message = "⬇️ Complaint volume decreasing. Good sign!"
                else:
                    trend = "stable"
                    message = "➡️ Complaint volume stable."
            else:
                trend = "insufficient_data"
                message = "Not enough data for trend analysis."
            
            return {
                'trend': trend,
                'message': message,
                'data': [{'date': c['date'], 'count': c['count']} for c in complaints_trend]
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    # ==================== ADMIN INSIGHTS ====================
    
    @staticmethod
    def _analyze_system_health(conn):
        """Analyze overall system health"""
        try:
            # Count active users
            total_students = conn.execute('SELECT COUNT(*) FROM students').fetchone()[0]
            total_faculty = conn.execute('SELECT COUNT(*) FROM faculty').fetchone()[0]
            total_admins = conn.execute('SELECT COUNT(*) FROM admin').fetchone()[0]
            
            # Count active content
            total_events = conn.execute('SELECT COUNT(*) FROM exam_events WHERE is_active = 1').fetchone()[0]
            total_assignments = conn.execute('SELECT COUNT(*) FROM assignments').fetchone()[0]
            total_notices = conn.execute('SELECT COUNT(*) FROM notices WHERE is_published = 1').fetchone()[0]
            
            # Calculate health score
            health_score = min(100, (
                (total_students > 0) * 20 +
                (total_faculty > 0) * 20 +
                (total_events > 0) * 20 +
                (total_assignments > 0) * 20 +
                (total_notices > 0) * 20
            ))
            
            if health_score >= 80:
                status = "excellent"
                message = "🟢 System is healthy and active"
            elif health_score >= 60:
                status = "good"
                message = "🟡 System is functioning well"
            else:
                status = "needs_attention"
                message = "🔴 System needs more content and users"
            
            return {
                'health_score': health_score,
                'status': status,
                'message': message,
                'users': {
                    'students': total_students,
                    'faculty': total_faculty,
                    'admins': total_admins
                },
                'content': {
                    'events': total_events,
                    'assignments': total_assignments,
                    'notices': total_notices
                }
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def _analyze_user_engagement(conn):
        """Analyze user engagement metrics"""
        try:
            # Recent activity (last 7 days)
            recent_complaints = conn.execute(
                'SELECT COUNT(*) FROM complaints WHERE created_at > datetime("now", "-7 days")'
            ).fetchone()[0]
            
            recent_submissions = conn.execute(
                'SELECT COUNT(*) FROM submissions WHERE submitted_at > datetime("now", "-7 days")'
            ).fetchone()[0]
            
            recent_events = conn.execute(
                'SELECT COUNT(*) FROM exam_events WHERE created_at > datetime("now", "-7 days")'
            ).fetchone()[0]
            
            # Calculate engagement score
            engagement_score = min(100, (recent_complaints * 5 + recent_submissions * 3 + recent_events * 10))
            
            if engagement_score >= 70:
                status = "high"
                message = "📈 High user engagement"
            elif engagement_score >= 40:
                status = "moderate"
                message = "📊 Moderate user engagement"
            else:
                status = "low"
                message = "📉 Low user engagement - consider promotional activities"
            
            return {
                'engagement_score': engagement_score,
                'status': status,
                'message': message,
                'recent_activity': {
                    'complaints': recent_complaints,
                    'submissions': recent_submissions,
                    'events': recent_events
                }
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def _analyze_event_effectiveness(conn):
        """Analyze event calendar effectiveness"""
        try:
            total_events = conn.execute('SELECT COUNT(*) FROM exam_events WHERE is_active = 1').fetchone()[0]
            upcoming_events = conn.execute(
                'SELECT COUNT(*) FROM exam_events WHERE is_active = 1 AND event_date >= date("now")'
            ).fetchone()[0]
            
            total_notifications = conn.execute('SELECT COUNT(*) FROM event_notifications').fetchone()[0]
            
            if total_events == 0:
                return {
                    'message': 'No events created yet',
                    'status': 'inactive'
                }
            
            notification_rate = (total_notifications / total_events) if total_events > 0 else 0
            
            return {
                'total_events': total_events,
                'upcoming_events': upcoming_events,
                'total_notifications': total_notifications,
                'notification_rate': round(notification_rate, 1),
                'message': f'📅 {upcoming_events} upcoming events, {total_notifications} notifications sent',
                'status': 'active' if upcoming_events > 0 else 'no_upcoming'
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def _analyze_assignment_system(conn):
        """Analyze assignment system usage"""
        try:
            total_assignments = conn.execute('SELECT COUNT(*) FROM assignments').fetchone()[0]
            total_submissions = conn.execute('SELECT COUNT(*) FROM submissions').fetchone()[0]
            
            if total_assignments == 0:
                return {
                    'message': 'No assignments created yet',
                    'status': 'inactive'
                }
            
            avg_submissions = total_submissions / total_assignments
            
            # Analyze bonus effectiveness
            bonus_awarded = conn.execute(
                'SELECT COUNT(*) FROM submissions WHERE bonus_points > 0'
            ).fetchone()[0]
            
            bonus_rate = (bonus_awarded / total_submissions * 100) if total_submissions > 0 else 0
            
            return {
                'total_assignments': total_assignments,
                'total_submissions': total_submissions,
                'avg_submissions': round(avg_submissions, 1),
                'bonus_awarded': bonus_awarded,
                'bonus_rate': round(bonus_rate, 1),
                'message': f'📝 {total_assignments} assignments, {bonus_rate:.1f}% early submissions',
                'status': 'active'
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def _generate_admin_recommendations(conn):
        """Generate AI recommendations for admin"""
        recommendations = []
        
        try:
            # Check for upcoming events
            upcoming_events = conn.execute(
                'SELECT COUNT(*) FROM exam_events WHERE is_active = 1 AND event_date BETWEEN date("now") AND date("now", "+7 days")'
            ).fetchone()[0]
            
            if upcoming_events == 0:
                recommendations.append({
                    'priority': 'medium',
                    'icon': '📅',
                    'title': 'Schedule Events',
                    'message': 'No events scheduled for the next 7 days. Consider adding upcoming exams or events.',
                    'action': 'Create Event',
                    'link': '/admin/event/create'
                })
            
            # Check for old notices
            old_notices = conn.execute(
                'SELECT COUNT(*) FROM notices WHERE is_published = 1 AND created_at < datetime("now", "-30 days")'
            ).fetchone()[0]
            
            if old_notices > 5:
                recommendations.append({
                    'priority': 'low',
                    'icon': '🗂️',
                    'title': 'Archive Old Notices',
                    'message': f'{old_notices} notices are over 30 days old. Consider archiving them.',
                    'action': 'Manage Notices',
                    'link': '/admin/manage_notices'
                })
            
            # Check system activity
            recent_activity = conn.execute(
                'SELECT COUNT(*) FROM complaints WHERE created_at > datetime("now", "-7 days")'
            ).fetchone()[0]
            
            if recent_activity == 0:
                recommendations.append({
                    'priority': 'info',
                    'icon': '💡',
                    'title': 'Low Activity',
                    'message': 'No complaints in the last 7 days. System is running smoothly!',
                    'action': None,
                    'link': None
                })
            
            if not recommendations:
                recommendations.append({
                    'priority': 'info',
                    'icon': '✅',
                    'title': 'System Running Smoothly',
                    'message': 'All systems operational. No urgent actions required.',
                    'action': None,
                    'link': None
                })
            
        except Exception as e:
            recommendations.append({
                'priority': 'error',
                'icon': '❌',
                'title': 'Error',
                'message': f'Unable to generate recommendations: {str(e)}',
                'action': None,
                'link': None
            })
        
        return recommendations
    
    @staticmethod
    def _generate_admin_alerts(conn):
        """Generate time-sensitive alerts for admin"""
        alerts = []
        
        try:
            # Check for events without notifications
            events_no_notif = conn.execute('''
                SELECT COUNT(*) FROM exam_events e
                LEFT JOIN event_notifications en ON e.id = en.event_id
                WHERE e.is_active = 1 AND en.id IS NULL
            ''').fetchone()[0]
            
            if events_no_notif > 0:
                alerts.append({
                    'type': 'warning',
                    'message': f'{events_no_notif} event(s) have no notifications sent',
                    'action': 'Review Events'
                })
            
            # Check for pending complaints system-wide
            pending_complaints = conn.execute(
                'SELECT COUNT(*) FROM complaints WHERE status = "pending"'
            ).fetchone()[0]
            
            if pending_complaints > 20:
                alerts.append({
                    'type': 'warning',
                    'message': f'{pending_complaints} complaints pending review system-wide',
                    'action': 'Notify Faculty'
                })
            
        except Exception as e:
            pass
        
        return alerts
    
    @staticmethod
    def _generate_predictions(conn):
        """Generate predictive insights"""
        predictions = []
        
        try:
            # Predict complaint volume
            recent_complaints = conn.execute(
                'SELECT COUNT(*) FROM complaints WHERE created_at > datetime("now", "-7 days")'
            ).fetchone()[0]
            
            older_complaints = conn.execute(
                'SELECT COUNT(*) FROM complaints WHERE created_at BETWEEN datetime("now", "-14 days") AND datetime("now", "-7 days")'
            ).fetchone()[0]
            
            if older_complaints > 0:
                trend = (recent_complaints - older_complaints) / older_complaints * 100
                
                if trend > 20:
                    predictions.append({
                        'type': 'warning',
                        'title': 'Complaint Volume Increasing',
                        'message': f'Complaints increased by {trend:.0f}% this week. Monitor faculty workload.',
                        'confidence': 'medium'
                    })
                elif trend < -20:
                    predictions.append({
                        'type': 'positive',
                        'title': 'Complaint Volume Decreasing',
                        'message': f'Complaints decreased by {abs(trend):.0f}% this week. Positive trend!',
                        'confidence': 'medium'
                    })
            
            # Predict assignment submission patterns
            upcoming_deadlines = conn.execute(
                'SELECT COUNT(*) FROM assignments WHERE deadline BETWEEN datetime("now") AND datetime("now", "+3 days")'
            ).fetchone()[0]
            
            if upcoming_deadlines > 5:
                predictions.append({
                    'type': 'info',
                    'title': 'High Submission Volume Expected',
                    'message': f'{upcoming_deadlines} assignment deadlines in next 3 days. Expect high activity.',
                    'confidence': 'high'
                })
            
        except Exception as e:
            pass
        
        return predictions

    
    # ==================== STUDENT INSIGHTS ====================
    
    @staticmethod
    def _analyze_student_assignments(student_id, conn):
        """Analyze student's assignment status"""
        try:
            # Get all assignments for student
            assignments = conn.execute('''
                SELECT a.id, a.title, a.deadline, a.reward_type,
                       s.id as submission_id, s.submission_time as submitted_at, 
                       s.ai_bonus_marks as bonus_points, s.is_verified
                FROM assignments a
                LEFT JOIN submissions s ON a.id = s.assignment_id AND s.student_id = ?
                ORDER BY a.deadline ASC
            ''', (student_id,)).fetchall()
            
            if not assignments:
                return {
                    'message': 'No assignments available',
                    'status': 'info'
                }
            
            total = len(assignments)
            submitted = sum(1 for a in assignments if a['submission_id'])
            pending = total - submitted
            graded = sum(1 for a in assignments if a['is_verified'])
            
            # Calculate bonus earned
            total_bonus = sum(a['bonus_points'] or 0 for a in assignments if a['bonus_points'])
            
            # Check upcoming deadlines (flexible datetime parsing)
            upcoming = []
            for a in assignments:
                if a['submission_id']:
                    continue  # Already submitted
                
                try:
                    deadline = parse_deadline(a['deadline'])
                    if deadline:
                        now = datetime.now()
                        if now < deadline < now + timedelta(days=3):
                            upcoming.append(a)
                except Exception as e:
                    print(f"Error parsing deadline: {e}")
                    continue
            
            if pending > 0:
                message = f"📝 {pending} assignment(s) pending submission"
                status = "pending"
            else:
                message = f"✅ All assignments submitted! Great work!"
                status = "complete"
            
            return {
                'total': total,
                'submitted': submitted,
                'pending': pending,
                'graded': graded,
                'total_bonus': round(total_bonus, 1),
                'upcoming_count': len(upcoming),
                'message': message,
                'status': status
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def _analyze_student_performance(student_id, conn):
        """Analyze student's academic performance"""
        try:
            # Get student marks
            marks = conn.execute('''
                SELECT subject, exam, marks
                FROM marks
                WHERE student_id = ?
            ''', (student_id,)).fetchall()
            
            if not marks:
                return {
                    'message': 'No marks data available yet',
                    'status': 'info'
                }
            
            # Define max marks for each exam type
            exam_max_marks = {
                'Insem-1': 20,
                'Insem-2': 20,
                'End Sem': 60
            }
            
            # Calculate overall percentage
            total_marks_obtained = 0
            total_marks_possible = 0
            subject_percentages = []
            
            for m in marks:
                max_marks = exam_max_marks.get(m['exam'], 100)
                total_marks_obtained += m['marks']
                total_marks_possible += max_marks
                
                # Calculate percentage for this subject
                percentage = (m['marks'] / max_marks) * 100
                subject_percentages.append((m['subject'], percentage))
            
            if total_marks_possible == 0:
                return {
                    'message': 'No marks data available',
                    'status': 'info'
                }
            
            percentage = (total_marks_obtained / total_marks_possible) * 100
            
            # Determine performance level
            if percentage >= 80:
                message = f"🌟 Excellent performance! Keep it up!"
                status = "excellent"
            elif percentage >= 60:
                message = f"✅ Good performance! You're doing well."
                status = "good"
            elif percentage >= 40:
                message = f"📊 Average performance. Room for improvement."
                status = "average"
            else:
                message = f"⚠️ Need to focus more. Seek help if needed."
                status = "needs_improvement"
            
            # Find best and worst subjects
            if subject_percentages:
                best_subject = max(subject_percentages, key=lambda x: x[1])
                worst_subject = min(subject_percentages, key=lambda x: x[1])
            else:
                best_subject = None
                worst_subject = None
            
            return {
                'percentage': round(percentage, 1),
                'total_subjects': len(marks),
                'message': message,
                'status': status,
                'best_subject': best_subject[0] if best_subject else None,
                'best_percentage': round(best_subject[1], 1) if best_subject else None,
                'worst_subject': worst_subject[0] if worst_subject else None,
                'worst_percentage': round(worst_subject[1], 1) if worst_subject else None
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def _get_student_upcoming_events(student_id, conn):
        """Get upcoming events for student"""
        try:
            # Get student details
            student = conn.execute(
                'SELECT department, semester FROM students WHERE id = ?',
                (student_id,)
            ).fetchone()
            
            if not student:
                return {
                    'message': 'Student not found',
                    'status': 'error'
                }
            
            # Get upcoming events (next 7 days)
            events = conn.execute('''
                SELECT title, event_date, start_time, event_type
                FROM exam_events
                WHERE is_active = 1 
                AND event_date >= date('now')
                AND event_date <= date('now', '+7 days')
                AND (
                    target_audience = 'all' OR
                    (target_audience = 'department' AND department = ?) OR
                    (target_audience = 'semester' AND semester = ?) OR
                    (target_audience = 'class' AND department = ? AND semester = ?)
                )
                ORDER BY event_date ASC, start_time ASC
                LIMIT 5
            ''', (student['department'], student['semester'], 
                  student['department'], student['semester'])).fetchall()
            
            if not events:
                return {
                    'count': 0,
                    'message': 'No upcoming events in the next 7 days',
                    'status': 'none'
                }
            
            return {
                'count': len(events),
                'events': [dict(e) for e in events],
                'message': f"📅 {len(events)} upcoming event(s) this week",
                'status': 'active'
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def _generate_student_recommendations(student_id, conn):
        """Generate AI recommendations for students"""
        recommendations = []
        
        try:
            # Check pending assignments
            pending_assignments = conn.execute('''
                SELECT a.id, a.title, a.deadline
                FROM assignments a
                LEFT JOIN submissions s ON a.id = s.assignment_id AND s.student_id = ?
                WHERE s.id IS NULL AND a.deadline > datetime('now')
                ORDER BY a.deadline ASC
            ''', (student_id,)).fetchall()
            
            # Check for urgent deadlines (within 3 days)
            urgent = []
            for a in pending_assignments:
                try:
                    deadline = parse_deadline(a['deadline'])
                    if deadline and deadline < datetime.now() + timedelta(days=3):
                        urgent.append(a)
                except Exception as e:
                    print(f"Error parsing deadline: {e}")
                    continue
            
            if urgent:
                recommendations.append({
                    'priority': 'high',
                    'icon': '⏰',
                    'title': 'Urgent Deadlines!',
                    'message': f'{len(urgent)} assignment(s) due within 3 days. Submit now to earn bonus points!',
                    'action': 'View Assignments',
                    'link': '/student/assignments'
                })
            elif pending_assignments:
                recommendations.append({
                    'priority': 'medium',
                    'icon': '📝',
                    'title': 'Pending Assignments',
                    'message': f'{len(pending_assignments)} assignment(s) awaiting submission. Submit early for bonus!',
                    'action': 'View Assignments',
                    'link': '/student/assignments'
                })
            
            # Check upcoming events
            student = conn.execute(
                'SELECT department, semester FROM students WHERE id = ?',
                (student_id,)
            ).fetchone()
            
            if student:
                upcoming_events = conn.execute('''
                    SELECT COUNT(*) FROM exam_events
                    WHERE is_active = 1 
                    AND event_date BETWEEN date('now') AND date('now', '+3 days')
                    AND (
                        target_audience = 'all' OR
                        (target_audience = 'department' AND department = ?) OR
                        (target_audience = 'semester' AND semester = ?) OR
                        (target_audience = 'class' AND department = ? AND semester = ?)
                    )
                ''', (student['department'], student['semester'],
                      student['department'], student['semester'])).fetchone()[0]
                
                if upcoming_events > 0:
                    recommendations.append({
                        'priority': 'medium',
                        'icon': '📅',
                        'title': 'Upcoming Events',
                        'message': f'{upcoming_events} event(s) scheduled in the next 3 days. Check your calendar!',
                        'action': 'View Calendar',
                        'link': '/student/calendar'
                    })
            
            # Check performance
            marks = conn.execute('''
                SELECT AVG(marks * 100.0 / 
                    CASE exam
                        WHEN 'Insem-1' THEN 20
                        WHEN 'Insem-2' THEN 20
                        WHEN 'End Sem' THEN 60
                        ELSE 100
                    END
                ) as avg_percentage
                FROM marks
                WHERE student_id = ?
            ''', (student_id,)).fetchone()
            
            if marks and marks['avg_percentage']:
                avg = marks['avg_percentage']
                if avg < 50:
                    recommendations.append({
                        'priority': 'high',
                        'icon': '📚',
                        'title': 'Focus on Studies',
                        'message': f'Your average is {avg:.1f}%. Consider seeking help from faculty or peers.',
                        'action': 'View Marks',
                        'link': '/student/internal_marks'
                    })
                elif avg >= 80:
                    recommendations.append({
                        'priority': 'info',
                        'icon': '🌟',
                        'title': 'Excellent Work!',
                        'message': f'Your average is {avg:.1f}%. Keep up the great work!',
                        'action': None,
                        'link': None
                    })
            
            # If no recommendations, add positive message
            if not recommendations:
                recommendations.append({
                    'priority': 'info',
                    'icon': '✅',
                    'title': 'All Caught Up!',
                    'message': 'No pending tasks. Great job staying on top of everything!',
                    'action': None,
                    'link': None
                })
            
        except Exception as e:
            recommendations.append({
                'priority': 'error',
                'icon': '❌',
                'title': 'Error',
                'message': f'Unable to generate recommendations: {str(e)}',
                'action': None,
                'link': None
            })
        
        return recommendations
    
    @staticmethod
    def _generate_student_alerts(student_id, conn):
        """Generate time-sensitive alerts for students"""
        alerts = []
        
        try:
            # Check for overdue assignments
            overdue = conn.execute('''
                SELECT COUNT(*) FROM assignments a
                LEFT JOIN submissions s ON a.id = s.assignment_id AND s.student_id = ?
                WHERE s.id IS NULL AND a.deadline < datetime('now')
            ''', (student_id,)).fetchone()[0]
            
            if overdue > 0:
                alerts.append({
                    'type': 'warning',
                    'message': f'{overdue} assignment(s) overdue! Contact faculty immediately.',
                    'action': 'View Assignments'
                })
            
            # Check for unread notices
            try:
                unread_notices = conn.execute(
                    'SELECT COUNT(*) FROM notices WHERE is_published = 1 AND created_at > datetime("now", "-7 days")'
                ).fetchone()[0]
                
                if unread_notices > 3:
                    alerts.append({
                        'type': 'info',
                        'message': f'{unread_notices} new notice(s) posted this week',
                        'action': 'View Notices'
                    })
            except:
                pass
            
        except Exception as e:
            pass
        
        return alerts
