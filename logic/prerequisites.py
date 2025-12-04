"""
Prerequisite filtering logic for course selection.

Ensures students only see courses they're eligible for based on prerequisites.
"""

import pandas as pd
import os
from collections import defaultdict

PREREQUISITES_FILE = "pre-requisites.csv"


def load_prerequisites() -> dict:
    """
    Load prerequisite chains from CSV.

    Returns:
        dict: {course_code: {'order': int, 'chain_id': str, 'alternatives': [list]}}

    Example structure:
        {
            'ENGL-110': {'order': 1, 'chain_id': 'ENGL', 'alternatives': []},
            'ENGL-120': {'order': 2, 'chain_id': 'ENGL', 'alternatives': []},
            'STAT-105': {'order': 2, 'chain_id': 'MATH', 'alternatives': ['THM-331']},
        }
    """
    if not os.path.exists(PREREQUISITES_FILE):
        return {}

    try:
        df = pd.read_csv(PREREQUISITES_FILE)

        # Build prerequisite chains
        prereq_data = {}
        chains = defaultdict(list)  # Track courses by chain

        for _, row in df.iterrows():
            order_str = str(row['Order']).strip()
            course_codes_str = str(row['Course Code']).strip()

            # Skip empty rows
            if not order_str or not course_codes_str or order_str == 'nan' or course_codes_str == 'nan':
                continue

            try:
                order = int(order_str)
            except (ValueError, TypeError):
                continue

            # Handle alternative courses (separated by /)
            course_codes = [c.strip() for c in course_codes_str.split('/')]
            primary_course = course_codes[0]
            alternatives = course_codes[1:] if len(course_codes) > 1 else []

            # Determine chain ID (use course prefix, e.g., 'ENGL', 'ACCT')
            chain_id = primary_course.split('-')[0]

            # Store each course code
            for course in course_codes:
                prereq_data[course] = {
                    'order': order,
                    'chain_id': chain_id,
                    'primary': primary_course,
                    'alternatives': alternatives if course == primary_course else []
                }
                chains[chain_id].append((order, course))

        return prereq_data

    except Exception as e:
        print(f"Error loading prerequisites: {e}")
        return {}


def find_chain_root(course_code: str, prereq_data: dict) -> str:
    """
    Find the root course (order=1) for a given course's chain.

    Args:
        course_code: The course to find the root for
        prereq_data: Prerequisite data from load_prerequisites()

    Returns:
        str: Chain ID (e.g., 'ENGL', 'ACCT')
    """
    if course_code not in prereq_data:
        return None

    return prereq_data[course_code]['chain_id']


def get_eligible_courses(student_courses_taken: list, all_required_courses: list,
                         prereq_data: dict) -> list:
    """
    Filter courses based on prerequisite requirements.

    Logic:
    - If student hasn't taken order=1 course, don't show any higher orders in that chain
    - If student has taken order=N, only show order=N+1 (not N+2 or higher)

    Args:
        student_courses_taken: List of course codes the student has completed
        all_required_courses: List of all courses required for the student's major
        prereq_data: Prerequisite data from load_prerequisites()

    Returns:
        list: Filtered list of courses the student is eligible for
    """
    if not prereq_data:
        # If no prerequisite data, return all required courses
        return all_required_courses

    # Group courses by chain
    chains = defaultdict(lambda: {'taken': [], 'available': []})
    courses_without_prereqs = []

    for course in all_required_courses:
        if course not in prereq_data:
            # Course has no prerequisites
            courses_without_prereqs.append(course)
        else:
            chain_id = prereq_data[course]['chain_id']
            order = prereq_data[course]['order']
            chains[chain_id]['available'].append((order, course))

    # Check what student has taken in each chain
    for course in student_courses_taken:
        if course in prereq_data:
            chain_id = prereq_data[course]['chain_id']
            order = prereq_data[course]['order']
            chains[chain_id]['taken'].append(order)

    # Determine eligible courses
    eligible = courses_without_prereqs.copy()

    for chain_id, chain_data in chains.items():
        if not chain_data['taken']:
            # Student hasn't taken any courses in this chain
            # Only show order=1 courses
            for order, course in chain_data['available']:
                if order == 1:
                    eligible.append(course)
        else:
            # Student has taken some courses in this chain
            # Show only the next order (max_taken + 1)
            max_taken = max(chain_data['taken'])
            for order, course in chain_data['available']:
                if order == max_taken + 1:
                    eligible.append(course)

    return eligible


def filter_student_requirements(student_id: str, major_code: str,
                                student_courses_taken: list,
                                requirements_df: pd.DataFrame,
                                prereq_data: dict) -> list:
    """
    Get filtered list of courses for a student based on prerequisites.

    This is the main function to use in the course matching flow.

    Args:
        student_id: Student ID
        major_code: Student's major code (e.g., 'TES-53E')
        student_courses_taken: List of courses the student has already taken
        requirements_df: Requirements DataFrame from curriculum_requirements2.csv
        prereq_data: Prerequisite data from load_prerequisites()

    Returns:
        list: Filtered list of required courses the student still needs AND is eligible for
    """
    if requirements_df.empty:
        return []

    # Extract major prefix
    major_prefix = major_code.split("-")[0] if "-" in major_code else major_code[:3]

    # Validate major exists
    available_majors = ['BAD', 'THM', 'FIN', 'TES', 'INT']
    if major_prefix not in available_majors:
        return []

    # Get courses where this major column has 'X'
    major_reqs = requirements_df[requirements_df[major_prefix] == 'X']
    required_codes = major_reqs['course_code'].tolist()

    # Find missing courses (not yet taken)
    missing_courses = [code for code in required_codes if code not in student_courses_taken]

    # Apply prerequisite filtering
    eligible_courses = get_eligible_courses(
        student_courses_taken,
        missing_courses,
        prereq_data
    )

    return eligible_courses
