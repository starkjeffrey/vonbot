Looking at the code, I can identify several significant performance issues. Let me analyze the main culprits:

## Root Causes of Slowness

### 1. **Database queries inside loops without caching** (Most Critical)

In `logic/course_matching.py`, the `generate_needs_matrix` function calls `get_student_requirements()` for each student, and each call:
- Reads the CSV file from disk (`load_requirements()`)
- Makes a database query to fetch the student's transcript

```python
# This happens for EVERY student in the loop
for i, (_, student) in enumerate(students_df.iterrows()):
    missing_courses = get_student_requirements(student_id, major_code)  # DB query + CSV read
```

### 2. **`get_course_last_offered()` called repeatedly in the UI**

In `app.py` (tabs[1]), after generating the needs matrix, there's another loop that calls `get_course_last_offered()` for every course with demand > 0:

```python
for course in course_cols:
    count = needs_df[course].sum()
    if count > 0:
        history = get_course_last_offered(course)  # DB query for EACH course!
```

This is executed on **every Streamlit rerun** if `needs_df` is in session state.

### 3. **No `@st.cache_data` or `@st.cache_resource` decorators**

None of the expensive operations are cached. Every widget interaction triggers a full script rerun, re-executing:
- CSV loading
- Database queries
- DataFrame computations

### 4. **`check_db_status()` runs on every rerun**

The sidebar calls `check_db_status()` unconditionally on every page load, making a database connection just to check connectivity.

---

## Recommended Fixes

Here's a refactored version with caching:

```python
# logic/course_matching.py - Add caching

import streamlit as st

@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_requirements():
    """Load requirements CSV - cached"""
    if os.path.exists(REQUIREMENTS_FILE):
        return pd.read_csv(REQUIREMENTS_FILE)
    return pd.DataFrame()

@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_all_transcripts(student_ids: tuple) -> dict:
    """Bulk fetch transcripts for all students at once"""
    if not student_ids:
        return {}
    
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
def get_course_last_offered_bulk(course_codes: tuple) -> dict:
    """Bulk fetch course history for multiple courses"""
    if not course_codes:
        return {}
    
    # Single query for all courses
    results = {}
    for code in course_codes:
        # Or better: use a single query with UNION ALL or cursor iteration
        results[code] = get_course_last_offered(code)
    return results
```

For the main app:

```python
# app.py - Add caching to DB check

@st.cache_data(ttl=30)  # Cache for 30 seconds
def check_db_status():
    try:
        from database.connection import get_db_connection
        conn = get_db_connection()
        conn.close()
        return True, None
    except Exception as e:
        return False, str(e)
```

And the critical fix for the demand calculation - **move it inside the button click** or cache it:

```python
# Only compute this ONCE when button is clicked, not on every rerun
if st.button("Generate Needs Matrix", type="primary"):
    # ... generate needs_df ...
    
    # Compute demand summary HERE, not outside the button
    demand_df = compute_demand_summary(needs_df)  # Make this a cached function
    st.session_state["demand_df"] = demand_df
```

Would you like me to create a fully refactored version of the key files with all these optimizations applied?
