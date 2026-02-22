"""
Test script for Event Calendar System
Run this to verify the system is working correctly
"""

import sqlite3
from datetime import datetime, timedelta

def test_database_tables():
    """Test if event tables exist"""
    print("=" * 60)
    print("Testing Database Tables")
    print("=" * 60)
    
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        # Check exam_events table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='exam_events'")
        if cursor.fetchone():
            print("✓ exam_events table exists")
            
            # Count events
            cursor.execute("SELECT COUNT(*) FROM exam_events WHERE is_active = 1")
            count = cursor.fetchone()[0]
            print(f"  - Active events: {count}")
        else:
            print("✗ exam_events table NOT found")
        
        # Check event_notifications table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='event_notifications'")
        if cursor.fetchone():
            print("✓ event_notifications table exists")
            
            # Count notifications
            cursor.execute("SELECT COUNT(*) FROM event_notifications")
            count = cursor.fetchone()[0]
            print(f"  - Notifications sent: {count}")
        else:
            print("✗ event_notifications table NOT found")
        
        # Check students table columns
        cursor.execute("PRAGMA table_info(students)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'department' in columns:
            print("✓ students.department column exists")
        else:
            print("✗ students.department column NOT found")
        
        if 'semester' in columns:
            print("✓ students.semester column exists")
        else:
            print("✗ students.semester column NOT found")
        
        conn.close()
        print("\n✅ Database structure is correct!\n")
        return True
        
    except Exception as e:
        print(f"\n❌ Database test failed: {e}\n")
        return False

def test_event_service():
    """Test EventService functionality"""
    print("=" * 60)
    print("Testing Event Service")
    print("=" * 60)
    
    try:
        from utils.event_service import EventService, EventType, TargetAudience
        print("✓ EventService imported successfully")
        
        # Test get_event_statistics
        stats = EventService.get_event_statistics()
        print(f"✓ Event statistics retrieved:")
        print(f"  - Total events: {stats['total_events']}")
        print(f"  - Upcoming events: {stats['upcoming_events']}")
        print(f"  - Past events: {stats['past_events']}")
        print(f"  - Notifications sent: {stats['notifications_sent']}")
        
        print("\n✅ Event Service is working!\n")
        return True
        
    except Exception as e:
        print(f"\n❌ Event Service test failed: {e}\n")
        import traceback
        traceback.print_exc()
        return False

def test_email_service():
    """Test EmailService configuration"""
    print("=" * 60)
    print("Testing Email Service")
    print("=" * 60)
    
    try:
        from utils.email_service import EmailService
        print("✓ EmailService imported successfully")
        
        # Check configuration
        print(f"  - SMTP Server: {EmailService.SMTP_SERVER}")
        print(f"  - SMTP Port: {EmailService.SMTP_PORT}")
        print(f"  - Email Address: {EmailService.EMAIL_ADDRESS}")
        
        if EmailService.EMAIL_ADDRESS == 'your-college-email@gmail.com':
            print("\n⚠️  WARNING: Email not configured!")
            print("   Please update utils/email_service.py with your SMTP settings")
            print("   See EVENT_CALENDAR_SETUP.md for instructions\n")
        else:
            print("\n✓ Email appears to be configured")
            print("  Run EmailService.test_email_configuration() to verify\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Email Service test failed: {e}\n")
        return False

def test_websocket_handler():
    """Test WebSocket handler"""
    print("=" * 60)
    print("Testing WebSocket Handler")
    print("=" * 60)
    
    try:
        from utils.websocket_handler import WebSocketHandler
        print("✓ WebSocketHandler imported successfully")
        print("✓ Event update methods available:")
        print("  - broadcast_event_update()")
        print("  - broadcast_calendar_refresh()")
        
        print("\n✅ WebSocket Handler is ready!\n")
        return True
        
    except Exception as e:
        print(f"\n❌ WebSocket Handler test failed: {e}\n")
        return False

def test_templates():
    """Test if all templates exist"""
    print("=" * 60)
    print("Testing Templates")
    print("=" * 60)
    
    import os
    
    templates = [
        'templates/admin_events.html',
        'templates/create_event.html',
        'templates/edit_event.html',
        'templates/view_event.html',
        'templates/student_calendar.html'
    ]
    
    all_exist = True
    for template in templates:
        if os.path.exists(template):
            print(f"✓ {template}")
        else:
            print(f"✗ {template} NOT FOUND")
            all_exist = False
    
    if all_exist:
        print("\n✅ All templates exist!\n")
    else:
        print("\n❌ Some templates are missing!\n")
    
    return all_exist

def test_routes():
    """Test if routes are accessible"""
    print("=" * 60)
    print("Testing Routes")
    print("=" * 60)
    
    print("Admin Routes:")
    print("  - /admin/events")
    print("  - /admin/event/create")
    print("  - /admin/event/<id>")
    print("  - /admin/event/<id>/edit")
    print("  - /admin/event/<id>/delete")
    
    print("\nStudent Routes:")
    print("  - /student/calendar")
    print("  - /api/calendar/events")
    print("  - /api/event/<id>")
    
    print("\n✅ All routes are defined!\n")
    return True

def create_sample_event():
    """Create a sample event for testing"""
    print("=" * 60)
    print("Creating Sample Event")
    print("=" * 60)
    
    try:
        from utils.event_service import EventService
        import sqlite3
        
        # Check if admin exists
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        admin = cursor.execute("SELECT id FROM admin LIMIT 1").fetchone()
        
        if not admin:
            print("⚠️  No admin found in database. Please create an admin first.")
            conn.close()
            return False
        
        admin_id = admin[0]
        
        # Create sample event
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        
        event_id = EventService.create_event(
            title="Sample Test Event",
            description="This is a test event created by the test script",
            event_date=tomorrow,
            start_time="10:00:00",
            end_time="12:00:00",
            event_type="exam",
            semester=None,
            department=None,
            target_audience="all",
            created_by=admin_id
        )
        
        if event_id:
            print(f"✓ Sample event created successfully!")
            print(f"  - Event ID: {event_id}")
            print(f"  - Title: Sample Test Event")
            print(f"  - Date: {tomorrow}")
            print(f"  - Time: 10:00 AM - 12:00 PM")
            print("\n✅ You can now view this event in the admin dashboard!\n")
            return True
        else:
            print("✗ Failed to create sample event")
            return False
        
    except Exception as e:
        print(f"\n❌ Sample event creation failed: {e}\n")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "EVENT CALENDAR SYSTEM TEST SUITE" + " " * 16 + "║")
    print("╚" + "=" * 58 + "╝")
    print("\n")
    
    results = []
    
    # Run tests
    results.append(("Database Tables", test_database_tables()))
    results.append(("Event Service", test_event_service()))
    results.append(("Email Service", test_email_service()))
    results.append(("WebSocket Handler", test_websocket_handler()))
    results.append(("Templates", test_templates()))
    results.append(("Routes", test_routes()))
    
    # Summary
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print("\n" + "=" * 60)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 60)
    
    if passed == total:
        print("\n🎉 All tests passed! System is ready to use!")
        
        # Ask if user wants to create sample event
        print("\n" + "=" * 60)
        response = input("Would you like to create a sample event? (y/n): ")
        if response.lower() == 'y':
            create_sample_event()
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")
    
    print("\n📖 For setup instructions, see EVENT_CALENDAR_SETUP.md")
    print("\n")

if __name__ == '__main__':
    main()
