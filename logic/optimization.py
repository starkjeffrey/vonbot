"""
Schedule optimization logic.

This module is already reasonably efficient as it operates on in-memory data.
Minor optimizations added for consistency.
"""

import pandas as pd
from collections import defaultdict

TIME_SLOTS = [
    # Morning slots
    "MW_0800",      # MW 8:00-9:30 AM
    "TTH_0800",     # TTH 8:00-9:30 AM
    "MW_0930",      # MW 9:30-11:00 AM
    "TTH_0930",     # TTH 9:30-11:00 AM
    "Fri_0800",     # Fri 8:00-11:00 AM
    "Sat_0800",     # Sat 8:00-11:00 AM
    # Evening slots
    "MW_1800",      # MW 6:00-7:30 PM
    "TTH_1800",     # TTH 6:00-7:30 PM
    "MW_1930",      # MW 7:30-9:00 PM
    "TTH_1930",     # TTH 7:30-9:00 PM
    "Fri_1800",     # Fri 6:00-9:00 PM
    "Sat_1800",     # Sat 6:00-9:00 PM
    # 3-hour evening classes (conflict with both time slots)
    "M_1800_3hr",   # M 6:00-9:00 PM
    "T_1800_3hr",   # T 6:00-9:00 PM
    "W_1800_3hr",   # W 6:00-9:00 PM
    "Th_1800_3hr",  # Th 6:00-9:00 PM
    "Fri_1800_3hr", # Fri 6:00-9:00 PM
]

# Human-readable labels for time slots
TIME_SLOT_LABELS = {
    # Morning
    "MW_0800": "MW 8:00-9:30 AM",
    "TTH_0800": "TTH 8:00-9:30 AM",
    "MW_0930": "MW 9:30-11:00 AM",
    "TTH_0930": "TTH 9:30-11:00 AM",
    "Fri_0800": "Fri 8:00-11:00 AM",
    "Sat_0800": "Sat 8:00-11:00 AM",
    # Evening
    "MW_1800": "MW 6:00-7:30 PM",
    "TTH_1800": "TTH 6:00-7:30 PM",
    "MW_1930": "MW 7:30-9:00 PM",
    "TTH_1930": "TTH 7:30-9:00 PM",
    "Fri_1800": "Fri 6:00-9:00 PM",
    "Sat_1800": "Sat 6:00-9:00 PM",
    # 3-hour
    "M_1800_3hr": "M 6:00-9:00 PM (3hr)",
    "T_1800_3hr": "T 6:00-9:00 PM (3hr)",
    "W_1800_3hr": "W 6:00-9:00 PM (3hr)",
    "Th_1800_3hr": "Th 6:00-9:00 PM (3hr)",
    "Fri_1800_3hr": "Fri 6:00-9:00 PM (3hr)",
}

# Conflict mapping: 3-hour classes conflict with these slots
TIME_SLOT_CONFLICTS = {
    "M_1800_3hr": ["MW_1800", "MW_1930"],      # Monday 6-9 conflicts with both MW slots
    "T_1800_3hr": ["TTH_1800", "TTH_1930"],    # Tuesday 6-9 conflicts with both TTH slots
    "W_1800_3hr": ["MW_1800", "MW_1930"],      # Wednesday 6-9 conflicts with both MW slots
    "Th_1800_3hr": ["TTH_1800", "TTH_1930"],   # Thursday 6-9 conflicts with both TTH slots
    "Fri_1800_3hr": ["Fri_1800"],              # Friday 6-9 conflicts with Fri 6-9
}


def get_time_slot_label(slot: str) -> str:
    """Get human-readable label for a time slot."""
    return TIME_SLOT_LABELS.get(slot, slot)


def slots_conflict(slot1: str, slot2: str) -> bool:
    """
    Check if two time slots conflict with each other.

    Args:
        slot1: First time slot code
        slot2: Second time slot code

    Returns:
        bool: True if slots conflict, False otherwise
    """
    if slot1 == slot2:
        return True

    # Check if slot1 is a 3-hour class that conflicts with slot2
    if slot1 in TIME_SLOT_CONFLICTS:
        if slot2 in TIME_SLOT_CONFLICTS[slot1]:
            return True

    # Check if slot2 is a 3-hour class that conflicts with slot1
    if slot2 in TIME_SLOT_CONFLICTS:
        if slot1 in TIME_SLOT_CONFLICTS[slot2]:
            return True

    return False


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

    # Check for conflicts (including 3-hour class conflicts)
    for student_id, enrollments in student_courses.items():
        # Check all pairs of courses for conflicts
        for i, (course1, slot1) in enumerate(enrollments):
            for course2, slot2 in enrollments[i+1:]:
                # Check if these slots conflict (handles same slot AND 3-hour conflicts)
                if slots_conflict(slot1, slot2):
                    conflicts.append({
                        "StudentId": student_id,
                        "Name": student_names.get(student_id, "Unknown"),
                        "ConflictSlot": f"{get_time_slot_label(slot1)} ↔ {get_time_slot_label(slot2)}",
                        "Courses": [course1, course2],
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