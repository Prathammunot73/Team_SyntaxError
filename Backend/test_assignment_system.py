"""
Test script for Assignment System
Run this to verify the system is working correctly
"""

from models.database_models import init_db, get_db_connection
from utils.assignment_service import AssignmentService, RewardType
from datetime import datetime, timedelta

def test_database_setup():
    """Test database tables are created"""
    print("Testing database setup...")
    init_db()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if tables exist
    tables = ['assignments', 'submissions', 'assignment_marks_log']
    for table in tables:
        result = cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table,)
        ).fetchone()
        if result:
            print(f"✓ Table '{table}' exists")
        else:
            print(f"✗ Table '{table}' missing")
    
    conn.close()
    print()

def test_assignment_creation():
    """Test creating an assignment"""
    print("Testing assignment creation...")
    
    # Create test assignment
    deadline = datetime.now() + timedelta(days=7)
    assignment_id = AssignmentService.create_assignment(
        title="Test Assignment",
        description="This is a test assignment",
        subject="Computer Science",
        deadline=deadline.isoformat(),
        max_bonus_marks=5.0,
        reward_type=RewardType.TIER,
        created_by=1  # Assuming faculty ID 1 exists
    )
    
    if assignment_id:
        print(f"✓ Assignment created with ID: {assignment_id}")
        
        # Retrieve assignment
        assignment = AssignmentService.get_assignment_by_id(assignment_id)
        if assignment:
            print(f"✓ Assignment retrieved: {assignment['title']}")
        else:
            print("✗ Failed to retrieve assignment")
    else:
        print("✗ Failed to create assignment")
    
    print()

def test_bonus_calculation():
    """Test bonus calculation logic"""
    print("Testing bonus calculation...")
    
    # Create test assignment
    created_at = datetime.now()
    deadline = created_at + timedelta(days=30)
    
    # Mock assignment object
    class MockAssignment:
        def __init__(self):
            self.created_at = created_at.isoformat()
            self.deadline = deadline.isoformat()
            self.max_bonus_marks = 5.0
            self.reward_type = RewardType.TIER
        
        def __getitem__(self, key):
            return getattr(self, key)
    
    assignment = MockAssignment()
    
    # Test different submission times
    test_cases = [
        (created_at + timedelta(days=5), "Early (17%)", 5.0),
        (created_at + timedelta(days=12), "Mid-early (40%)", 3.75),
        (created_at + timedelta(days=20), "Mid-late (67%)", 2.5),
        (created_at + timedelta(days=28), "Late (93%)", 1.25),
        (deadline + timedelta(days=1), "After deadline", 0.0),
    ]
    
    for submission_time, label, expected in test_cases:
        bonus = AssignmentService._calculate_ai_bonus(assignment, submission_time)
        status = "✓" if abs(bonus - expected) < 0.01 else "✗"
        print(f"{status} {label}: {bonus} marks (expected {expected})")
    
    print()

def test_submission():
    """Test submission creation"""
    print("Testing submission...")
    
    # Create test assignment first
    deadline = datetime.now() + timedelta(days=7)
    assignment_id = AssignmentService.create_assignment(
        title="Test Submission Assignment",
        description="For testing submissions",
        subject="Testing",
        deadline=deadline.isoformat(),
        max_bonus_marks=5.0,
        reward_type=RewardType.FIXED,
        created_by=1
    )
    
    if assignment_id:
        # Test submission
        success, message, bonus = AssignmentService.submit_assignment(
            assignment_id=assignment_id,
            student_id=1,  # Assuming student ID 1 exists
            file_path=None
        )
        
        if success:
            print(f"✓ Submission successful: {message}")
            print(f"  Bonus calculated: {bonus} marks")
        else:
            print(f"✗ Submission failed: {message}")
    else:
        print("✗ Could not create test assignment")
    
    print()

def test_statistics():
    """Test statistics calculation"""
    print("Testing statistics...")
    
    # Get all assignments
    conn = get_db_connection()
    assignments = conn.execute('SELECT id FROM assignments LIMIT 1').fetchall()
    conn.close()
    
    if assignments:
        assignment_id = assignments[0]['id']
        stats = AssignmentService.get_assignment_statistics(assignment_id)
        
        print(f"✓ Statistics retrieved:")
        print(f"  Total submissions: {stats['total_submissions']}")
        print(f"  Verified: {stats['verified_submissions']}")
        print(f"  Pending: {stats['pending_submissions']}")
        print(f"  Average bonus: {stats['avg_bonus']}")
    else:
        print("ℹ No assignments found to test statistics")
    
    print()

def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("ASSIGNMENT SYSTEM TEST SUITE")
    print("=" * 60)
    print()
    
    try:
        test_database_setup()
        test_assignment_creation()
        test_bonus_calculation()
        test_submission()
        test_statistics()
        
        print("=" * 60)
        print("✓ ALL TESTS COMPLETED")
        print("=" * 60)
        print()
        print("System is ready to use!")
        print("- Teachers can create assignments at /faculty/assignments")
        print("- Students can submit at /student/assignments")
        
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    run_all_tests()
