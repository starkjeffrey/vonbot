import pandas as pd
import os
from database.connection import db_cursor

# Load requirements CSV
REQUIREMENTS_FILE = "curriculum_canonical_requirements_majors_1-6.csv"

def load_requirements():
    if os.path.exists(REQUIREMENTS_FILE):
        try:
            # Use python engine and skip bad lines to be robust
            return pd.read_csv(REQUIREMENTS_FILE, on_bad_lines='skip', engine='python')
        except Exception as e:
            print(f"Error reading requirements CSV: {e}")
            return pd.DataFrame()
    return pd.DataFrame()

def get_student_requirements(student_id: str, major_code: str):
    """
    Get list of courses required for the student's major that they haven't taken.
    
    Args:
        student_id (str): Student ID.
        major_code (str): Student's BatchIDForMaster (e.g., 'TES-53E').
        
    Returns:
        list: List of required course names/IDs.
    """
    requirements_df = load_requirements()
    if requirements_df.empty:
        return []

    # Map major code to major_id in CSV (This mapping needs to be defined or inferred)
    # For now, we'll try to infer from the major code prefix (e.g., 'TES' -> 5, 'INT' -> 6, 'BAD' -> 1?)
    # Based on CSV content: 
    # 1 -> Business? (ACCT, BUS, MGT)
    # 3 -> Tourism (THM)
    # 4 -> Finance (FIN)
    # 5 -> TESOL (EDUC, ENGL)
    # 6 -> IR (POL, IR)
    
    major_prefix = major_code.split('-')[0] if '-' in major_code else major_code[:3]
    major_map = {
        'BAD': 1, # Business Admin?
        'THM': 3, # Tourism
        'FIN': 4, # Finance
        'TES': 5, # TESOL
        'INT': 6, # International Relations
        # Add others as needed
    }
    
    major_id = major_map.get(major_prefix)
    if not major_id:
        return []
        
    # Filter requirements for this major
    major_reqs = requirements_df[requirements_df['major_id'] == major_id]['name'].tolist()
    
    # Clean up course names (remove description if present, e.g., "ACCT-300 - Cost Accounting I" -> "ACCT-300")
    # The SQL example used 'LAW-273', 'LAW-301A'. CSV has "LAW-273 - Business Law".
    # We need to extract the code.
    required_codes = [req.split(' - ')[0].split(':')[0].strip() for req in major_reqs]
    
    # Check what the student has already taken (passed)
    # Using the logic from potential_class_takers.sql: grade < 'F' or (termid in ('2023T2') and grade in ('IP','I'))
    # We need to query the DB for this student's transcript
    
    taken_courses = []
    query = """
    SELECT coursecode 
    FROM vw_BAlatestgrade 
    WHERE id = %s 
    AND (grade < 'F' OR grade IN ('IP', 'I')) -- Simplified passing logic
    """
    
    try:
        with db_cursor() as cursor:
            cursor.execute(query, (student_id,))
            rows = cursor.fetchall()
            taken_courses = [row['coursecode'] for row in rows]
    except Exception as e:
        print(f"Error fetching transcript for {student_id}: {e}")
        # If DB fails, assume nothing taken to be safe (or handle otherwise)
        
    # Find missing courses
    missing_courses = [code for code in required_codes if code not in taken_courses]
    
    return missing_courses

    return missing_courses

def get_course_last_offered(course_code: str):
    """
    Check when a course was last offered.
    Returns:
        dict: {'TermName': str, 'StartDate': date, 'MonthsAgo': int}
    """
    # Note: AcademicCourseTakers does not have TermId column. 
    # We must parse it from ClassId (format: TermId!$CourseId!$Section)
    query = """
    SELECT TOP 1 
        t.TermName, 
        t.StartDate, 
        DATEDIFF(month, t.StartDate, GETDATE()) as MonthsAgo
    FROM AcademicCourseTakers act
    JOIN Terms t ON LEFT(act.ClassId, CHARINDEX('!$', act.ClassId) - 1) = t.TermId
    WHERE act.ClassId LIKE %s
    AND CHARINDEX('!$', act.ClassId) > 0
    ORDER BY t.StartDate DESC
    """
    try:
        with db_cursor() as cursor:
            cursor.execute(query, (f'%{course_code}%',))
            row = cursor.fetchone()
            return row if row else None
    except Exception as e:
        print(f"Error fetching history for {course_code}: {e}")
        return None

def generate_needs_matrix(students_df: pd.DataFrame, progress_callback=None):
    """
    Generate a matrix of students and their required courses.
    
    Args:
        students_df (pd.DataFrame): DataFrame of active students.
        progress_callback (callable, optional): Function accepting (current_count, total_count, current_student_name).
        
    Returns:
        pd.DataFrame: Matrix with columns [StudentId, Name, Major, Cohort, LastEnroll, Course1, Course2, ...]
    """
    if students_df.empty:
        return pd.DataFrame()
        
    all_needs = []
    total_students = len(students_df)
    
    # Pre-load requirements to avoid reading CSV in loop
    requirements_df = load_requirements()
    
    # Optimization: Fetch all transcripts for these students in one go?
    # For now, we'll loop, but in production, bulk fetch is better.
    
    for i, (_, student) in enumerate(students_df.iterrows()):
        student_id = student['StudentId']
        student_name = student['Name']
        major_code = student['MajorCode']
        
        if progress_callback:
            progress_callback(i + 1, total_students, student_name)
        
        # We need to pass the pre-loaded requirements_df to avoid re-reading, 
        # but get_student_requirements currently reads it. 
        # Let's refactor get_student_requirements slightly or just call it.
        # For speed in this prototype, we'll just call it.
        missing_courses = get_student_requirements(student_id, major_code)
        
        student_data = {
            'StudentId': student_id,
            'Name': student_name,
            'Email': student.get('Email', ''),
            'Major': major_code,
            'Cohort': student.get('Cohort', ''),
            'LastEnroll': student['LastActiveDate']
        }
        
        for course in missing_courses:
            student_data[course] = 1
            
        all_needs.append(student_data)
        
    if not all_needs:
        return pd.DataFrame()
        
    needs_df = pd.DataFrame(all_needs)
    
    # Fill NaNs with 0 (not needed)
    # Identify course columns (those not in metadata)
    metadata_cols = ['StudentId', 'Name', 'Email', 'Major', 'Cohort', 'LastEnroll']
    course_cols = [c for c in needs_df.columns if c not in metadata_cols]
    
    needs_df[course_cols] = needs_df[course_cols].fillna(0)
    
    return needs_df
