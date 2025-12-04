"""
Prerequisite filtering logic for course selection.

Ensures students only see courses they're eligible for based on prerequisites.

Key concepts:
- There are 15 explicit chains (a-o)
- A course can appear in multiple chains (e.g., ARIL-210 is in chains b,c,d,e)
- A course can appear in multiple chains (e.g., MATH-101 is in chains m,n)
- For a course to be shown, the student must have completed ALL prior courses
  in at least ONE chain that contains that course
"""

import pandas as pd
import os
from collections import defaultdict

PREREQUISITES_FILE = "pre-requisites.csv"


def load_prerequisites() -> dict:
    """
    Load prerequisite chains from CSV.

    Returns:
        dict: {
            'chains': {chain_id: [(order, course_code), ...]},
            'course_to_chains': {course_code: [(chain_id, order), ...]}
        }

    Example structure:
        {
            'chains': {
                'a': [(1, 'ACCT-310'), (2, 'ACCT-312'), (3, 'ACCT-313'), (4, 'ACCT-300')],
                'b': [(1, 'ARIL-210'), (2, 'ENGL-201A'), (3, 'ENGL-302A')],
                ...
            },
            'course_to_chains': {
                'ACCT-310': [('a', 1)],
                'ARIL-210': [('b', 1), ('c', 1), ('d', 1), ('e', 1)],
                'STAT-105': [('m', 2)],
                'THM-331': [('n', 2)],
                ...
            }
        }
    """
    if not os.path.exists(PREREQUISITES_FILE):
        return {'chains': {}, 'course_to_chains': {}}

    try:
        df = pd.read_csv(PREREQUISITES_FILE)

        chains = defaultdict(list)
        course_to_chains = defaultdict(list)

        for _, row in df.iterrows():
            chain_id = str(row['ChainID']).strip()
            order_str = str(row['Order']).strip()
            course_code = str(row['CourseCode']).strip()

            # Skip empty rows
            if not chain_id or not order_str or not course_code:
                continue
            if chain_id == 'nan' or order_str == 'nan' or course_code == 'nan':
                continue

            try:
                order = int(order_str)
            except (ValueError, TypeError):
                continue

            # Add to chain
            chains[chain_id].append((order, course_code))

            # Map course to its chains
            course_to_chains[course_code].append((chain_id, order))

        # Sort each chain by order
        for chain_id in chains:
            chains[chain_id] = sorted(chains[chain_id], key=lambda x: x[0])

        return {
            'chains': dict(chains),
            'course_to_chains': dict(course_to_chains)
        }

    except Exception as e:
        print(f"Error loading prerequisites: {e}")
        return {'chains': {}, 'course_to_chains': {}}


def get_chain_progress(chain_id: str, student_courses_taken: list, prereq_data: dict) -> int:
    """
    Get the highest order completed in a chain by a student.

    Args:
        chain_id: The chain identifier (a-o)
        student_courses_taken: List of course codes the student has completed
        prereq_data: Prerequisite data from load_prerequisites()

    Returns:
        int: Highest order completed (0 if none taken)
    """
    chain = prereq_data['chains'].get(chain_id, [])
    if not chain:
        return 0

    max_completed = 0
    for order, course_code in chain:
        if course_code in student_courses_taken:
            max_completed = max(max_completed, order)

    return max_completed


def is_course_eligible(course_code: str, student_courses_taken: list, prereq_data: dict) -> bool:
    """
    Check if a student is eligible to take a course based on prerequisites.

    A course is eligible if:
    1. It's not in any prerequisite chain (no prerequisites), OR
    2. In at least ONE chain containing this course, the student has completed
       all prior courses (i.e., all courses with lower order numbers)

    Args:
        course_code: The course to check eligibility for
        student_courses_taken: List of course codes the student has completed
        prereq_data: Prerequisite data from load_prerequisites()

    Returns:
        bool: True if student is eligible, False otherwise
    """
    course_to_chains = prereq_data.get('course_to_chains', {})
    chains = prereq_data.get('chains', {})

    # If course is not in any chain, it has no prerequisites
    if course_code not in course_to_chains:
        return True

    # Check each chain this course belongs to
    for chain_id, course_order in course_to_chains[course_code]:
        chain = chains.get(chain_id, [])

        # If this is the first course in the chain (order=1), it's always eligible
        if course_order == 1:
            return True

        # Check if student has completed all prior courses in this chain
        all_prior_completed = True
        for order, prereq_course in chain:
            if order < course_order:
                if prereq_course not in student_courses_taken:
                    all_prior_completed = False
                    break

        # If all prior courses in THIS chain are completed, course is eligible
        if all_prior_completed:
            return True

    # No chain allows this course yet
    return False


def is_next_in_chain(course_code: str, student_courses_taken: list, prereq_data: dict) -> bool:
    """
    Check if a course is the NEXT course to take in at least one chain.

    This prevents showing courses that are too far ahead in the chain.
    For example, if student hasn't taken ACCT-312, don't show ACCT-313 or ACCT-300.

    Args:
        course_code: The course to check
        student_courses_taken: List of course codes the student has completed
        prereq_data: Prerequisite data from load_prerequisites()

    Returns:
        bool: True if course is the next one in at least one chain
    """
    course_to_chains = prereq_data.get('course_to_chains', {})
    chains = prereq_data.get('chains', {})

    # If course is not in any chain, it's always available
    if course_code not in course_to_chains:
        return True

    # Check each chain this course belongs to
    for chain_id, course_order in course_to_chains[course_code]:
        chain = chains.get(chain_id, [])

        # Get the highest order the student has completed in this chain
        max_completed = 0
        for order, chain_course in chain:
            if chain_course in student_courses_taken:
                max_completed = max(max_completed, order)

        # This course is "next" if its order is exactly max_completed + 1
        if course_order == max_completed + 1:
            return True

    # Not the next course in any chain
    return False


def get_eligible_courses(student_courses_taken: list, all_required_courses: list,
                         prereq_data: dict) -> list:
    """
    Filter courses based on prerequisite requirements.

    Logic:
    - If a course is not in any chain, it's always eligible
    - If a course is in a chain, only show it if:
      1. It's the next course in at least one chain (student has completed all prior)
      2. Student hasn't already taken it

    Args:
        student_courses_taken: List of course codes the student has completed
        all_required_courses: List of all courses required for the student's major
        prereq_data: Prerequisite data from load_prerequisites()

    Returns:
        list: Filtered list of courses the student is eligible for
    """
    if not prereq_data or not prereq_data.get('chains'):
        # If no prerequisite data, return all required courses
        return all_required_courses

    eligible = []

    for course in all_required_courses:
        # Skip if student already took this course
        if course in student_courses_taken:
            continue

        # Check if course is the next one in at least one chain
        if is_next_in_chain(course, student_courses_taken, prereq_data):
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
