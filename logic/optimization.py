"""
Schedule optimization logic.

This module is already reasonably efficient as it operates on in-memory data.
Minor optimizations added for consistency.
"""

import pandas as pd
from collections import defaultdict

TIME_SLOTS = [
    "MW_1800",
    "MW_1930",
    "TTh_1800",
    "TTh_1930",
    "Sat_AM",
    "Sat_PM",
    "Fri_Eve",
]


def check_roster_conflicts(offered_courses: dict, rosters: dict) -> list:
    """
    Check for scheduling conflicts based on rosters and offered course slots.

    This version uses rosters (actual assigned students) instead of needs_matrix.

    Args:
        offered_courses: {CourseCode: TimeSlot}
        rosters: {CourseCode: [list of student dicts]}

    Returns:
        list: List of conflict dictionaries
    """
    conflicts = []

    if not offered_courses or not rosters:
        return conflicts

    # Build a map of student -> courses they're enrolled in
    student_courses = defaultdict(list)
    student_names = {}

    for course, students in rosters.items():
        if course in offered_courses:
            slot = offered_courses[course]
            if slot and slot != "Unassigned":
                for student in students:
                    sid = student["StudentId"]
                    student_courses[sid].append((course, slot))
                    student_names[sid] = student.get("Name", "Unknown")

    # Check for conflicts (same student, same slot, different courses)
    for student_id, enrollments in student_courses.items():
        # Group by slot
        slot_courses = defaultdict(list)
        for course, slot in enrollments:
            slot_courses[slot].append(course)

        # Find conflicts
        for slot, courses in slot_courses.items():
            if len(courses) > 1:
                conflicts.append({
                    "StudentId": student_id,
                    "Name": student_names.get(student_id, "Unknown"),
                    "ConflictSlot": slot,
                    "Courses": courses,
                })

    return conflicts


def check_conflicts(offered_courses: dict, needs_matrix: pd.DataFrame) -> list:
    """
    Check for scheduling conflicts based on student needs and offered course slots.

    DEPRECATED: Use check_roster_conflicts instead for actual roster-based conflicts.
    This is kept for backward compatibility.

    Args:
        offered_courses: {CourseCode: TimeSlot}
        needs_matrix: Students x Courses matrix

    Returns:
        list: List of conflict dictionaries
    """
    conflicts = []

    if needs_matrix.empty or not offered_courses:
        return conflicts

    offered_codes = list(offered_courses.keys())

    # Filter to only offered courses that exist in the matrix
    available_courses = [c for c in offered_codes if c in needs_matrix.columns]

    if not available_courses:
        return conflicts

    relevant_cols = ["StudentId", "Name"] + available_courses
    relevant_needs = needs_matrix[relevant_cols]

    for _, row in relevant_needs.iterrows():
        student_id = row["StudentId"]
        student_name = row["Name"]

        # Group needed courses by assigned slot
        slot_usage = defaultdict(list)

        for course in available_courses:
            if row[course] == 1:  # Student needs this course
                slot = offered_courses.get(course)
                if slot and slot != "Unassigned":
                    slot_usage[slot].append(course)

        # Check for multiple courses in the same slot
        for slot, courses in slot_usage.items():
            if len(courses) > 1:
                conflicts.append({
                    "StudentId": student_id,
                    "Name": student_name,
                    "ConflictSlot": slot,
                    "Courses": courses,
                })

    return conflicts


def optimize_schedule(student_list: list, available_courses: list) -> list:
    """
    Placeholder for auto-optimization if needed later.

    Could implement:
    - Constraint satisfaction solver
    - Genetic algorithm for schedule optimization
    - Graph coloring for conflict minimization
    """
    return []