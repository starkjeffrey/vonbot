from logic.course_matching import get_course_last_offered
from database.connection import db_cursor

def test_history():
    # Test with a few known courses
    test_courses = ['ACCT-300', 'LAW-273', 'BUS-360', 'NON-EXISTENT']
    
    print("--- Testing Course History Logic ---")
    
    for course in test_courses:
        print(f"\nChecking history for: {course}")
        history = get_course_last_offered(course)
        
        if history:
            print(f"✅ Found: {history}")
        else:
            print(f"❌ No history found (or error).")

    # Also inspect raw ClassId to verify parsing logic
    print("\n--- Inspecting Raw ClassId Samples ---")
    query = "SELECT TOP 5 ClassId FROM AcademicCourseTakers WHERE ClassId LIKE '%ACCT%'"
    try:
        with db_cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
            for row in rows:
                print(row)
    except Exception as e:
        print(f"Error inspecting ClassId: {e}")

if __name__ == "__main__":
    test_history()
