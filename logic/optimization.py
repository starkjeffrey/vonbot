import pandas as pd
from collections import defaultdict

TIME_SLOTS = [
    "MW_1800", "MW_1930",
    "TTh_1800", "TTh_1930",
    "Sat_AM", "Sat_PM",
    "Fri_Eve"
]

def check_conflicts(offered_courses: dict, needs_matrix: pd.DataFrame):
    """
    Check for scheduling conflicts based on student needs and offered course slots.
    
    Args:
        offered_courses (dict): {CourseCode: TimeSlot}
        needs_matrix (pd.DataFrame): Students x Courses matrix.
        
    Returns:
        list: List of conflict dictionaries [{'StudentId': str, 'Name': str, 'ConflictSlot': str, 'Courses': list}]
    """
    conflicts = []
    
    if needs_matrix.empty or not offered_courses:
        return conflicts
        
    # Filter needs matrix to only include offered courses
    offered_codes = list(offered_courses.keys())
    relevant_needs = needs_matrix[['StudentId', 'Name'] + [c for c in offered_codes if c in needs_matrix.columns]]
    
    for _, row in relevant_needs.iterrows():
        student_id = row['StudentId']
        student_name = row['Name']
        
        # Group needed courses by assigned slot
        slot_usage = defaultdict(list)
        
        for course in offered_codes:
            if course in row and row[course] == 1: # Student needs this course
                slot = offered_courses[course]
                if slot: # If slot is assigned
                    slot_usage[slot].append(course)
        
        # Check for multiple courses in the same slot
        for slot, courses in slot_usage.items():
            if len(courses) > 1:
                conflicts.append({
                    'StudentId': student_id,
                    'Name': student_name,
                    'ConflictSlot': slot,
                    'Courses': courses
                })
                
    return conflicts

def optimize_schedule(student_list, available_courses):
    """
    Placeholder for auto-optimization if needed later.
    """
    return []
