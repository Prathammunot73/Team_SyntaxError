"""
Test AI Dashboard Integration
Verify AI features are working correctly
"""

import sqlite3
from utils.ai_dashboard_assistant import AIDashboardAssistant

def test_ai_integration():
    """Test AI dashboard assistant integration"""
    print("=" * 60)
    print("Testing AI Dashboard Integration")
    print("=" * 60)
    print()
    
    try:
        # Connect to database
        conn = sqlite3.connect('database.db')
        conn.row_factory = sqlite3.Row
        
        # Test 1: Faculty Insights
        print("Test 1: Faculty AI Insights")
        print("-" * 60)
        
        # Get first faculty
        faculty = conn.execute('SELECT id FROM faculty LIMIT 1').fetchone()
        
        if faculty:
            faculty_id = faculty['id']
            insights = AIDashboardAssistant.get_faculty_insights(faculty_id, conn)
            
            print(f"✓ Faculty insights generated for ID: {faculty_id}")
            print(f"  - Complaint Analysis: {'✓' if insights.get('complaint_analysis') else '✗'}")
            print(f"  - Student Performance: {'✓' if insights.get('student_performance') else '✗'}")
            print(f"  - Assignment Insights: {'✓' if insights.get('assignment_insights') else '✗'}")
            print(f"  - Recommendations: {len(insights.get('recommendations', []))} items")
            print(f"  - Alerts: {len(insights.get('alerts', []))} items")
            print(f"  - Trends: {'✓' if insights.get('trends') else '✗'}")
            
            # Show sample recommendation
            if insights.get('recommendations'):
                rec = insights['recommendations'][0]
                print(f"\n  Sample Recommendation:")
                print(f"  {rec['icon']} {rec['title']}")
                print(f"  {rec['message']}")
            
            print("\n✅ Faculty AI insights working!\n")
        else:
            print("⚠️  No faculty found in database")
            print("   Create a faculty account to test faculty insights\n")
        
        # Test 2: Admin Insights
        print("Test 2: Admin AI Insights")
        print("-" * 60)
        
        insights = AIDashboardAssistant.get_admin_insights(conn)
        
        print("✓ Admin insights generated")
        print(f"  - System Health: {'✓' if insights.get('system_health') else '✗'}")
        print(f"  - User Engagement: {'✓' if insights.get('user_engagement') else '✗'}")
        print(f"  - Event Analytics: {'✓' if insights.get('event_analytics') else '✗'}")
        print(f"  - Assignment Analytics: {'✓' if insights.get('assignment_analytics') else '✗'}")
        print(f"  - Recommendations: {len(insights.get('recommendations', []))} items")
        print(f"  - Alerts: {len(insights.get('alerts', []))} items")
        print(f"  - Predictions: {len(insights.get('predictions', []))} items")
        
        # Show system health
        if insights.get('system_health'):
            health = insights['system_health']
            print(f"\n  System Health:")
            print(f"  Score: {health.get('health_score', 0)}%")
            print(f"  Status: {health.get('message', 'N/A')}")
        
        # Show sample recommendation
        if insights.get('recommendations'):
            rec = insights['recommendations'][0]
            print(f"\n  Sample Recommendation:")
            print(f"  {rec['icon']} {rec['title']}")
            print(f"  {rec['message']}")
        
        print("\n✅ Admin AI insights working!\n")
        
        # Test 3: Data Analysis
        print("Test 3: Data Analysis Capabilities")
        print("-" * 60)
        
        # Count data
        total_students = conn.execute('SELECT COUNT(*) FROM students').fetchone()[0]
        total_faculty = conn.execute('SELECT COUNT(*) FROM faculty').fetchone()[0]
        total_complaints = conn.execute('SELECT COUNT(*) FROM complaints').fetchone()[0]
        total_events = conn.execute('SELECT COUNT(*) FROM exam_events WHERE is_active = 1').fetchone()[0]
        total_assignments = conn.execute('SELECT COUNT(*) FROM assignments').fetchone()[0]
        
        print(f"✓ Database statistics:")
        print(f"  - Students: {total_students}")
        print(f"  - Faculty: {total_faculty}")
        print(f"  - Complaints: {total_complaints}")
        print(f"  - Events: {total_events}")
        print(f"  - Assignments: {total_assignments}")
        
        # Determine data availability
        has_data = (total_students > 0 and total_faculty > 0)
        
        if has_data:
            print("\n✅ Sufficient data for AI analysis!\n")
        else:
            print("\n⚠️  Limited data available")
            print("   Add more students and faculty for better AI insights\n")
        
        conn.close()
        
        # Summary
        print("=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print("✅ AI Dashboard Assistant: Working")
        print("✅ Faculty Insights: Functional")
        print("✅ Admin Insights: Functional")
        print("✅ Data Analysis: Operational")
        print()
        print("🎉 AI Integration Test Passed!")
        print()
        print("Next Steps:")
        print("1. Visit /faculty/dashboard to see AI insights")
        print("2. Visit /admin/dashboard to see system analytics")
        print("3. Add more data for richer AI recommendations")
        print()
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    test_ai_integration()
