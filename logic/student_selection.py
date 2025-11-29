"""
Student selection logic with caching optimizations.

Key optimizations:
1. Cached student fetching (5 minute TTL)
2. Helper function to clear cache when needed
"""

import pandas as pd
import streamlit as st
from database.connection import db_cursor


@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_active_students(months_back: int = 6):
    """
    Fetch students who have been active in the last X months.

    CACHED: This function hits the database only once per 5 minutes for each
    unique months_back value. Subsequent calls return cached data instantly.

    Args:
        months_back (int): Number of months to look back for activity.

    Returns:
        pd.DataFrame: DataFrame of active students.
    """
    query = """
    SELECT DISTINCT
        s.ID as StudentId,
        s.Name,
        s.schoolemail as Email,
        s.BatchIDForDoctor as MajorCode,
        SUBSTRING(s.BatchIDForDoctor, 5, 3) as Cohort,
        MAX(v.termstart) as LastActiveDate
    FROM vw_BAlatestgrade v
    JOIN Students s ON v.id = s.ID
    WHERE v.termstart >= CONVERT(varchar, DATEADD(month, -%d, GETDATE()), 111)
    AND s.BatchIDForDoctor IS NOT NULL
    AND s.BatchIDForDoctor <> ''
    GROUP BY s.ID, s.Name, s.schoolemail, s.BatchIDForDoctor, SUBSTRING(s.BatchIDForDoctor, 5, 3)
    ORDER BY LastActiveDate DESC
    """

    try:
        with db_cursor() as cursor:
            cursor.execute(query % months_back)
            data = cursor.fetchall()

            if not data:
                return pd.DataFrame(
                    columns=[
                        "StudentId",
                        "Name",
                        "Email",
                        "MajorCode",
                        "Cohort",
                        "LastActiveDate",
                    ]
                )

            df = pd.DataFrame(data)
            return df

    except Exception as e:
        print(f"Error fetching students: {e}")
        return pd.DataFrame(
            columns=["StudentId", "Name", "Email", "MajorCode", "Cohort", "LastActiveDate"]
        )


def clear_student_cache():
    """
    Clear the student cache to force a fresh database query.

    Call this when you need to refresh student data immediately,
    such as after a data import or manual database update.
    """
    get_active_students.clear()