"""
Disk caching for session data.

Saves intermediate results to disk so work persists across sessions.
"""

import os
import json
import pandas as pd
from datetime import datetime

CACHE_DIR = "cache"


def ensure_cache_dir():
    """Create cache directory if it doesn't exist."""
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)


def save_session_data(session_state: dict) -> str:
    """
    Save session state data to disk.

    Args:
        session_state: Streamlit session state dict

    Returns:
        str: Path to saved cache file
    """
    ensure_cache_dir()

    cache_data = {
        "saved_at": datetime.now().isoformat(),
        "students_df": None,
        "needs_df": None,
        "demand_df": None,
        "rosters": None,
        "offered_courses": None,
        "final_schedule": None,
        "months_option": None,
        "telegram_chat_id": None,
        "telegram_draft": None,
    }

    # Save DataFrames as JSON
    if "students_df" in session_state and session_state["students_df"] is not None:
        df = session_state["students_df"]
        if not df.empty:
            cache_data["students_df"] = df.to_dict(orient="records")

    if "needs_df" in session_state and session_state["needs_df"] is not None:
        df = session_state["needs_df"]
        if not df.empty:
            cache_data["needs_df"] = df.to_dict(orient="records")

    if "demand_df" in session_state and session_state["demand_df"] is not None:
        df = session_state["demand_df"]
        if not df.empty:
            cache_data["demand_df"] = df.to_dict(orient="records")

    # Save dicts directly
    if "rosters" in session_state:
        cache_data["rosters"] = session_state["rosters"]

    if "offered_courses" in session_state:
        cache_data["offered_courses"] = session_state["offered_courses"]

    if "final_schedule" in session_state:
        cache_data["final_schedule"] = session_state["final_schedule"]

    if "months_option" in session_state:
        cache_data["months_option"] = session_state["months_option"]

    # Save communications drafts
    if "telegram_chat_id" in session_state:
        cache_data["telegram_chat_id"] = session_state["telegram_chat_id"]

    if "telegram_draft" in session_state:
        cache_data["telegram_draft"] = session_state["telegram_draft"]

    # Save to file
    cache_file = os.path.join(CACHE_DIR, "session_cache.json")
    with open(cache_file, "w") as f:
        json.dump(cache_data, f, indent=2, default=str)

    return cache_file


def load_session_data() -> dict:
    """
    Load session state data from disk.

    Returns:
        dict: Loaded session data, or empty dict if no cache exists
    """
    cache_file = os.path.join(CACHE_DIR, "session_cache.json")

    if not os.path.exists(cache_file):
        return {}

    try:
        with open(cache_file, "r") as f:
            cache_data = json.load(f)

        result = {
            "saved_at": cache_data.get("saved_at"),
            "months_option": cache_data.get("months_option"),
            "telegram_chat_id": cache_data.get("telegram_chat_id"),
            "telegram_draft": cache_data.get("telegram_draft"),
        }

        # Convert lists back to DataFrames
        if cache_data.get("students_df"):
            result["students_df"] = pd.DataFrame(cache_data["students_df"])

        if cache_data.get("needs_df"):
            result["needs_df"] = pd.DataFrame(cache_data["needs_df"])

        if cache_data.get("demand_df"):
            result["demand_df"] = pd.DataFrame(cache_data["demand_df"])

        # Load dicts directly
        if cache_data.get("rosters"):
            result["rosters"] = cache_data["rosters"]

        if cache_data.get("offered_courses"):
            result["offered_courses"] = cache_data["offered_courses"]

        if cache_data.get("final_schedule"):
            result["final_schedule"] = cache_data["final_schedule"]

        return result

    except Exception as e:
        print(f"Error loading cache: {e}")
        return {}


def clear_cache():
    """Delete all cached data."""
    cache_file = os.path.join(CACHE_DIR, "session_cache.json")
    if os.path.exists(cache_file):
        os.remove(cache_file)


def get_cache_info() -> dict:
    """Get information about the current cache."""
    cache_file = os.path.join(CACHE_DIR, "session_cache.json")

    if not os.path.exists(cache_file):
        return {"exists": False}

    try:
        stat = os.stat(cache_file)
        with open(cache_file, "r") as f:
            data = json.load(f)

        return {
            "exists": True,
            "file_size": stat.st_size,
            "saved_at": data.get("saved_at"),
            "has_students": data.get("students_df") is not None,
            "has_needs": data.get("needs_df") is not None,
            "has_rosters": data.get("rosters") is not None and len(data.get("rosters", {})) > 0,
            "roster_count": len(data.get("rosters", {})) if data.get("rosters") else 0,
        }
    except Exception as e:
        return {"exists": True, "error": str(e)}


def get_student_course_counts(rosters: dict) -> dict:
    """
    Count how many courses each student is assigned to.

    Args:
        rosters: Dict of {course: [student dicts]}

    Returns:
        dict: {student_id: {"name": str, "count": int, "courses": [list]}}
    """
    student_counts = {}

    for course, students in rosters.items():
        for student in students:
            sid = student["StudentId"]
            if sid not in student_counts:
                student_counts[sid] = {
                    "StudentId": sid,
                    "Name": student.get("Name", "Unknown"),
                    "Major": student.get("Major", ""),
                    "Cohort": student.get("Cohort", ""),
                    "count": 0,
                    "courses": []
                }
            student_counts[sid]["count"] += 1
            student_counts[sid]["courses"].append(course)

    return student_counts


BACKUP_DIR = os.path.join(CACHE_DIR, "backups")


def ensure_backup_dir():
    """Create backup directory if it doesn't exist."""
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)


def create_backup(session_state: dict) -> str:
    """
    Create a timestamped backup snapshot of the current session.

    Args:
        session_state: Streamlit session state dict

    Returns:
        str: Path to created backup file
    """
    ensure_backup_dir()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(BACKUP_DIR, f"backup_{timestamp}.json")

    # Use the same save logic as save_session_data
    cache_data = {
        "saved_at": datetime.now().isoformat(),
        "students_df": None,
        "needs_df": None,
        "demand_df": None,
        "rosters": None,
        "offered_courses": None,
        "final_schedule": None,
        "months_option": None,
        "telegram_chat_id": None,
        "telegram_draft": None,
    }

    # Save DataFrames as JSON
    if "students_df" in session_state and session_state["students_df"] is not None:
        df = session_state["students_df"]
        if not df.empty:
            cache_data["students_df"] = df.to_dict(orient="records")

    if "needs_df" in session_state and session_state["needs_df"] is not None:
        df = session_state["needs_df"]
        if not df.empty:
            cache_data["needs_df"] = df.to_dict(orient="records")

    if "demand_df" in session_state and session_state["demand_df"] is not None:
        df = session_state["demand_df"]
        if not df.empty:
            cache_data["demand_df"] = df.to_dict(orient="records")

    # Save dicts directly
    if "rosters" in session_state:
        cache_data["rosters"] = session_state["rosters"]

    if "offered_courses" in session_state:
        cache_data["offered_courses"] = session_state["offered_courses"]

    if "final_schedule" in session_state:
        cache_data["final_schedule"] = session_state["final_schedule"]

    if "months_option" in session_state:
        cache_data["months_option"] = session_state["months_option"]

    # Save communications drafts
    if "telegram_chat_id" in session_state:
        cache_data["telegram_chat_id"] = session_state["telegram_chat_id"]

    if "telegram_draft" in session_state:
        cache_data["telegram_draft"] = session_state["telegram_draft"]

    # Save to backup file
    with open(backup_file, "w") as f:
        json.dump(cache_data, f, indent=2, default=str)

    return backup_file


def list_backups() -> list:
    """
    List all available backup snapshots.

    Returns:
        list: List of dicts with backup info [{filename, timestamp, size}]
    """
    ensure_backup_dir()

    backups = []
    for filename in os.listdir(BACKUP_DIR):
        if filename.startswith("backup_") and filename.endswith(".json"):
            filepath = os.path.join(BACKUP_DIR, filename)
            stat = os.stat(filepath)

            # Extract timestamp from filename
            timestamp_str = filename.replace("backup_", "").replace(".json", "")
            try:
                timestamp = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                display_time = timestamp.strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                display_time = timestamp_str

            backups.append({
                "filename": filename,
                "filepath": filepath,
                "timestamp": display_time,
                "size": stat.st_size,
            })

    # Sort by filename (which sorts by timestamp)
    backups.sort(key=lambda x: x["filename"], reverse=True)
    return backups


def restore_backup(backup_filename: str) -> dict:
    """
    Restore session state from a backup snapshot.

    Args:
        backup_filename: Name of the backup file to restore

    Returns:
        dict: Restored session data, or empty dict if restore fails
    """
    backup_file = os.path.join(BACKUP_DIR, backup_filename)

    if not os.path.exists(backup_file):
        return {}

    try:
        with open(backup_file, "r") as f:
            cache_data = json.load(f)

        result = {
            "saved_at": cache_data.get("saved_at"),
            "months_option": cache_data.get("months_option"),
            "telegram_chat_id": cache_data.get("telegram_chat_id"),
            "telegram_draft": cache_data.get("telegram_draft"),
        }

        # Convert lists back to DataFrames
        if cache_data.get("students_df"):
            result["students_df"] = pd.DataFrame(cache_data["students_df"])

        if cache_data.get("needs_df"):
            result["needs_df"] = pd.DataFrame(cache_data["needs_df"])

        if cache_data.get("demand_df"):
            result["demand_df"] = pd.DataFrame(cache_data["demand_df"])

        # Load dicts directly
        if cache_data.get("rosters"):
            result["rosters"] = cache_data["rosters"]

        if cache_data.get("offered_courses"):
            result["offered_courses"] = cache_data["offered_courses"]

        if cache_data.get("final_schedule"):
            result["final_schedule"] = cache_data["final_schedule"]

        return result

    except Exception as e:
        print(f"Error restoring backup: {e}")
        return {}


def delete_backup(backup_filename: str):
    """Delete a specific backup file."""
    backup_file = os.path.join(BACKUP_DIR, backup_filename)
    if os.path.exists(backup_file):
        os.remove(backup_file)
