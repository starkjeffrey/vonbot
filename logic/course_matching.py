"""
Course matching logic with performance optimizations.

Key optimizations:
1. Cached CSV loading (1 hour TTL)
2. Bulk transcript fetching (single query for all students)
3. Bulk course history fetching (single query for all courses)
4. Cached demand summary computation
"""

import pandas as pd
import os
import streamlit as st
from database.connection import db_cursor

# Load requirements CSV (simplified version with just course codes and major columns)
REQUIREMENTS_FILE = "curriculum_requirements.csv"


@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_requirements():
    """Load simplified requirements CSV with columns: course_code, BAD, THM, FIN, TES, INT.

    CACHED: This function reads from disk only once per hour.
    """
    if os.path.exists(REQUIREMENTS_FILE):
        try:
            return pd.read_csv(REQUIREMENTS_FILE)
        except Exception as e:
            print(f"Error reading requirements CSV: {e}")
            return pd.DataFrame()
    return pd.DataFrame()


@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_bulk_transcripts(student_ids: tuple) -> dict:
    """
    Bulk fetch transcripts for all students in a single query.

    OPTIMIZATION: Instead of N queries for N students, this makes 1 query.

    Args:
        student_ids: Tuple of student IDs (tuple for hashability/caching)

    Returns:
        dict: {student_id: [list of course codes they've taken]}
    """
    if not student_ids:
        return {}

    # Build parameterized query
    placeholders = ','.join(['%s'] * len(student_ids))
    query = f"""
    SELECT id, coursecode
    FROM vw_BAlatestgrade
    WHERE id IN ({placeholders})
    AND (grade < 'F' OR grade IN ('IP', 'I'))
    """

    results = {}
    try:
        with db_cursor() as cursor:
            cursor.execute(query, student_ids)
            for row in cursor.fetchall():
                student_id = row["id"]
                if student_id not in results:
                    results[student_id] = []
                results[student_id].append(row["coursecode"])
    except Exception as e:
        print(f"Error bulk fetching transcripts: {e}")

    return results


@st.cache_data(ttl=600)  # Cache for 10 minutes
def get_bulk_course_history(course_codes: tuple) -> dict:
    """
    Bulk fetch course offering history for multiple courses.

    OPTIMIZATION: Instead of N queries for N courses, fetches all at once.

    Args:
        course_codes: Tuple of course codes (tuple for hashability/caching)

    Returns:
        dict: {course_code: {'TermName': str, 'StartDate': date, 'MonthsAgo': int} or None}
    """
    if not course_codes:
        return {}

    results = {code: None for code in course_codes}

    # Query to get most recent offering for each course
    # Using a CTE to rank by date and get the most recent
    query = """
    WITH RankedOfferings AS (
        SELECT
            SUBSTRING(act.ClassId, CHARINDEX('!$', act.ClassId) + 2,
                CHARINDEX('!$', act.ClassId, CHARINDEX('!$', act.ClassId) + 2) - CHARINDEX('!$', act.ClassId) - 2) as CourseCode,
            t.TermName,
            t.StartDate,
            DATEDIFF(month, t.StartDate, GETDATE()) as MonthsAgo,
            ROW_NUMBER() OVER (
                PARTITION BY SUBSTRING(act.ClassId, CHARINDEX('!$', act.ClassId) + 2,
                    CHARINDEX('!$', act.ClassId, CHARINDEX('!$', act.ClassId) + 2) - CHARINDEX('!$', act.ClassId) - 2)
                ORDER BY t.StartDate DESC
            ) as rn
        FROM AcademicCourseTakers act
        JOIN Terms t ON LEFT(act.ClassId, CHARINDEX('!$', act.ClassId) - 1) = t.TermId
        WHERE CHARINDEX('!$', act.ClassId) > 0
    )
    SELECT CourseCode, TermName, StartDate, MonthsAgo
    FROM RankedOfferings
    WHERE rn = 1
    """

    try:
        with db_cursor() as cursor:
            cursor.execute(query)
            for row in cursor.fetchall():
                course_code = row["CourseCode"]
                if course_code in results:
                    results[course_code] = {
                        "TermName": row["TermName"],
                        "StartDate": row["StartDate"],
                        "MonthsAgo": row["MonthsAgo"]
                    }
    except Exception as e:
        print(f"Error bulk fetching course history: {e}")
        # Fallback to individual queries if bulk fails
        for code in course_codes:
            results[code] = get_course_last_offered(code)

    return results


def get_student_requirements_fast(student_id: str, major_code: str,
                                   requirements_df: pd.DataFrame,
                                   transcripts: dict) -> list:
    """
    Get list of courses required for the student's major that they haven't taken.

    OPTIMIZATION: Uses pre-loaded requirements and bulk-fetched transcripts
    instead of making database calls.

    Args:
        student_id: Student ID
        major_code: Student's BatchIDForDoctor (e.g., 'TES-53E')
        requirements_df: Pre-loaded requirements DataFrame
        transcripts: Pre-fetched dict of {student_id: [courses taken]}

    Returns:
        list: List of required course codes the student still needs
    """
    if requirements_df.empty:
        return []

    # Extract major prefix from BatchIDForDoctor (e.g., 'TES-53E' -> 'TES')
    major_prefix = major_code.split("-")[0] if "-" in major_code else major_code[:3]

    # Validate major exists in CSV columns
    available_majors = ['BAD', 'THM', 'FIN', 'TES', 'INT']
    if major_prefix not in available_majors:
        return []

    # Get courses where this major column has 'X'
    major_reqs = requirements_df[requirements_df[major_prefix] == 'X']
    required_codes = major_reqs['course_code'].tolist()

    # Get courses this student has taken from pre-fetched data
    taken_courses = transcripts.get(student_id, [])

    # Find missing courses
    missing_courses = [code for code in required_codes if code not in taken_courses]

    return missing_courses


def get_student_requirements(student_id: str, major_code: str):
    """
    Get list of courses required for the student's major that they haven't taken.

    DEPRECATED: Use get_student_requirements_fast() with bulk data for better performance.
    This function is kept for backward compatibility.

    Args:
        student_id (str): Student ID.
        major_code (str): Student's BatchIDForDoctor (e.g., 'TES-53E').

    Returns:
        list: List of required course names/IDs.
    """
    requirements_df = load_requirements()
    if requirements_df.empty:
        return []

    # Extract major prefix from BatchIDForDoctor (e.g., 'TES-53E' -> 'TES')
    major_prefix = major_code.split("-")[0] if "-" in major_code else major_code[:3]

    # Validate major exists in CSV columns
    available_majors = ['BAD', 'THM', 'FIN', 'TES', 'INT']
    if major_prefix not in available_majors:
        return []

    # Get courses where this major column has 'X'
    major_reqs = requirements_df[requirements_df[major_prefix] == 'X']
    required_codes = major_reqs['course_code'].tolist()

    # Check what the student has already taken (passed)
    taken_courses = []
    query = """
    SELECT coursecode
    FROM vw_BAlatestgrade
    WHERE id = %s
    AND (grade < 'F' OR grade IN ('IP', 'I'))
    """

    try:
        with db_cursor() as cursor:
            cursor.execute(query, (student_id,))
            rows = cursor.fetchall()
            taken_courses = [row["coursecode"] for row in rows]
    except Exception as e:
        print(f"Error fetching transcript for {student_id}: {e}")

    # Find missing courses
    missing_courses = [code for code in required_codes if code not in taken_courses]

    return missing_courses


def get_course_last_offered(course_code: str):
    """
    Check when a course was last offered.

    NOTE: For bulk operations, use get_bulk_course_history() instead.

    Returns:
        dict: {'TermName': str, 'StartDate': date, 'MonthsAgo': int}
    """
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
            cursor.execute(query, (f"%{course_code}%",))
            row = cursor.fetchone()
            return row if row else None
    except Exception as e:
        print(f"Error fetching history for {course_code}: {e}")
        return None


def generate_needs_matrix(students_df: pd.DataFrame, progress_callback=None):
    """
    Generate a matrix of students and their required courses.

    OPTIMIZED: Uses bulk transcript fetching instead of N individual queries.

    Args:
        students_df (pd.DataFrame): DataFrame of active students.
        progress_callback (callable, optional): Function accepting (current_count, total_count, current_student_name).

    Returns:
        pd.DataFrame: Matrix with columns [StudentId, Name, Major, Cohort, LastEnroll, Course1, Course2, ...]
    """
    if students_df.empty:
        return pd.DataFrame()

    # Pre-load requirements (cached)
    requirements_df = load_requirements()

    # OPTIMIZATION: Bulk fetch all transcripts in ONE query
    student_ids = tuple(students_df["StudentId"].tolist())
    transcripts = get_bulk_transcripts(student_ids)

    all_needs = []
    total_students = len(students_df)

    for i, (_, student) in enumerate(students_df.iterrows()):
        student_id = student["StudentId"]
        student_name = student["Name"]
        major_code = student["MajorCode"]

        if progress_callback:
            progress_callback(i + 1, total_students, student_name)

        # Use fast version with pre-loaded data
        missing_courses = get_student_requirements_fast(
            student_id, major_code, requirements_df, transcripts
        )

        student_data = {
            "StudentId": student_id,
            "Name": student_name,
            "Email": student.get("Email", ""),
            "Major": major_code,
            "Cohort": student.get("Cohort", ""),
            "LastEnroll": student["LastActiveDate"],
        }

        for course in missing_courses:
            student_data[course] = 1

        all_needs.append(student_data)

    if not all_needs:
        return pd.DataFrame()

    needs_df = pd.DataFrame(all_needs)

    # Fill NaNs with 0 (not needed)
    metadata_cols = ["StudentId", "Name", "Email", "Major", "Cohort", "LastEnroll"]
    course_cols = [c for c in needs_df.columns if c not in metadata_cols]

    needs_df[course_cols] = needs_df[course_cols].fillna(0)

    return needs_df


@st.cache_data(ttl=300)  # Cache for 5 minutes
def compute_demand_summary(_df_hash: str, needs_df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute course demand summary with history - CACHED.

    This function is called ONCE when the needs matrix is generated,
    not on every Streamlit rerun.

    Args:
        _df_hash: Hash of the needs_df for cache invalidation (underscore prefix = not displayed)
        needs_df: The needs matrix DataFrame

    Returns:
        pd.DataFrame: Summary with columns [Course, Demand, Last Offered, Months Ago]
    """
    if needs_df.empty:
        return pd.DataFrame(columns=["Course", "Demand", "Last Offered", "Months Ago"])

    metadata_cols = ["StudentId", "Name", "Email", "Major", "Cohort", "LastEnroll"]
    course_cols = [c for c in needs_df.columns if c not in metadata_cols]

    # Calculate demand for each course
    demand_data = []
    courses_with_demand = []

    for course in course_cols:
        count = int(needs_df[course].sum())
        if count > 0:
            courses_with_demand.append(course)
            demand_data.append({"Course": course, "Demand": count})

    if not demand_data:
        return pd.DataFrame(columns=["Course", "Demand", "Last Offered", "Months Ago"])

    # OPTIMIZATION: Bulk fetch course history for all courses at once
    course_history = get_bulk_course_history(tuple(courses_with_demand))

    # Combine demand with history
    for item in demand_data:
        course = item["Course"]
        history = course_history.get(course)
        if history:
            item["Last Offered"] = history.get("StartDate")
            item["Months Ago"] = history.get("MonthsAgo", 0)
        else:
            item["Last Offered"] = None
            item["Months Ago"] = 999  # Never offered

    return pd.DataFrame(demand_data)


def clear_course_cache():
    """Clear all course-related caches. Call when data needs refreshing."""
    load_requirements.clear()
    get_bulk_transcripts.clear()
    get_bulk_course_history.clear()
    compute_demand_summary.clear()