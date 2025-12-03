"""
Academic Scheduling Tool - Optimized Streamlit Application

Key optimizations:
1. Database status check is cached (not checked on every rerun)
2. Heavy imports are deferred until needed
3. Demand summary computed once and cached
4. No repeated database calls on widget interactions
5. Disk caching for session persistence across restarts
"""

import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import course display helpers
from logic.course_matching import load_requirements, format_course_with_title

st.set_page_config(
    page_title="Academic Scheduling Tool",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def check_login():
    """Check if user is authenticated."""
    return st.session_state.get("authenticated", False)


def login_page():
    """Display login page."""
    st.title("🎓 Academic Scheduling Tool")
    st.subheader("Admin Login")

    # Center the login form
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login", type="primary", use_container_width=True)

            if submit:
                admin_user = os.getenv("ADMIN_USERNAME", "admin")
                admin_pass = os.getenv("ADMIN_PASSWORD", "admin")

                if username == admin_user and password == admin_pass:
                    st.session_state["authenticated"] = True
                    st.session_state["username"] = username
                    st.rerun()
                else:
                    st.error("Invalid username or password")

        st.caption("Contact IT support if you need access.")


def load_cached_session():
    """Load cached session data on startup."""
    if "cache_loaded" not in st.session_state:
        from logic.cache import load_session_data
        cached = load_session_data()
        if cached:
            for key, value in cached.items():
                if key != "saved_at" and value is not None:
                    st.session_state[key] = value
            st.session_state["cache_loaded"] = True
            st.session_state["cache_saved_at"] = cached.get("saved_at")
        else:
            st.session_state["cache_loaded"] = True


def save_current_session():
    """Save current session to disk."""
    from logic.cache import save_session_data
    save_session_data(st.session_state)


# Load cache on startup
load_cached_session()


def remove_student_from_roster(course: str, student_id: str):
    """Remove a student from a specific course roster."""
    if "rosters" in st.session_state and course in st.session_state["rosters"]:
        st.session_state["rosters"][course] = [
            s for s in st.session_state["rosters"][course]
            if s["StudentId"] != student_id
        ]
        # Auto-save after roster change
        save_current_session()


@st.cache_data(ttl=30, show_spinner=False)  # Cache for 30 seconds
def check_db_status():
    """Check database connection status - CACHED to avoid repeated connections."""
    try:
        from database.connection import get_db_connection
        conn = get_db_connection()
        conn.close()
        return True, None
    except Exception as e:
        return False, str(e)


def main():
    st.title("🎓 Academic Scheduling Tool")

    # Sidebar for navigation and global settings
    with st.sidebar:
        # Show logged in user and logout button
        st.caption(f"👤 Logged in as: **{st.session_state.get('username', 'Admin')}**")
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state["authenticated"] = False
            st.session_state["username"] = None
            st.rerun()

        st.divider()
        st.header("Navigation")
        app_mode = st.radio("Go to", ["Admin Dashboard", "Student Portal"])

        st.divider()
        st.header("System Status")

        # Cached DB check - won't hit DB on every rerun
        is_connected, error_msg = check_db_status()
        if is_connected:
            st.write("Database: 🟢 Connected")
        else:
            st.write("Database: 🔴 Disconnected")
            if error_msg:
                st.error(f"Error: {error_msg}")

        # Button to force refresh DB status
        if st.button("🔄 Refresh Status", key="refresh_db"):
            check_db_status.clear()
            st.rerun()

        st.divider()
        st.header("💾 Session Cache")

        # Show cache status
        from logic.cache import get_cache_info, clear_cache
        cache_info = get_cache_info()

        if cache_info.get("exists"):
            if cache_info.get("saved_at"):
                st.caption(f"Last saved: {cache_info['saved_at'][:19]}")
            if cache_info.get("has_rosters"):
                st.caption(f"Rosters: {cache_info['roster_count']} classes")
        else:
            st.caption("No saved session")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Save", key="save_session", help="Save current work to disk"):
                save_current_session()
                st.success("Saved!")
                st.rerun()
        with col2:
            if st.button("🗑️ Clear", key="clear_cache", help="Delete saved session"):
                clear_cache()
                st.info("Cache cleared")
                st.rerun()

    if app_mode == "Admin Dashboard":
        admin_dashboard()
    elif app_mode == "Student Portal":
        student_portal()


def admin_dashboard():
    st.header("Admin Dashboard")

    tabs = st.tabs([
        "Student Selection",
        "Course Matching",
        "Class Rosters",
        "Manage Rosters",
        "Schedule Optimization",
        "Communications",
    ])

    with tabs[0]:
        render_student_selection_tab()

    with tabs[1]:
        render_course_matching_tab()

    with tabs[2]:
        render_class_rosters_tab()

    with tabs[3]:
        render_manage_rosters_tab()

    with tabs[4]:
        render_schedule_optimization_tab()

    with tabs[5]:
        render_communications_tab()


def render_student_selection_tab():
    """Student Selection Tab - with cached data fetching."""
    st.subheader("Select Active Students")
    st.write("Filter students based on recent activity.")

    col1, col2 = st.columns([1, 3])

    with col1:
        months_option = st.selectbox(
            "Activity Period",
            options=[6, 12, 18, 24],
            format_func=lambda x: f"Last {x} months",
            index=0,
        )

        if st.button("Fetch Students", type="primary"):
            with st.spinner("Fetching students from database..."):
                # Import here to avoid loading on every page load
                from logic.student_selection import get_active_students

                # This is now CACHED - subsequent calls with same months_option are instant
                students_df = get_active_students(months_option)
                st.session_state["students_df"] = students_df
                st.session_state["months_option"] = months_option
                save_current_session()  # Auto-save
                st.success(f"Found {len(students_df)} active students.")

        # Select a student to view requirements
        if "students_df" in st.session_state and not st.session_state[
            "students_df"].empty:
            students_df = st.session_state["students_df"]
            st.selectbox(
                "Select Student to View Requirements",
                options=students_df["StudentId"].tolist(),
                format_func=lambda
                    x: f"{x} - {students_df[students_df['StudentId'] == x].iloc[0]['Name']}",
            )
        else:
            st.info("Fetch students first to select one.")

    with col2:
        if "students_df" in st.session_state and not st.session_state[
            "students_df"].empty:
            st.dataframe(
                st.session_state["students_df"],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "StudentId": "ID",
                    "Name": "Name",
                    "Email": "Email",
                    "MajorCode": "Major Code",
                    "Cohort": "Cohort",
                    "LastActiveDate": st.column_config.DateColumn("Last Active"),
                },
            )
        elif "students_df" in st.session_state:
            st.info("No students found for the selected criteria.")


def render_course_matching_tab():
    """Course Matching Tab - with optimized bulk operations."""
    st.subheader("Match Courses")
    st.write("Match students to required courses.")

    if "students_df" not in st.session_state or st.session_state["students_df"].empty:
        st.warning("Please fetch students in the 'Student Selection' tab first.")
        return

    students_df = st.session_state["students_df"]

    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("Generate Needs Matrix", type="primary"):
            progress_bar = st.progress(0, text="Starting analysis...")

            def update_progress(current, total, name):
                percent = int((current / total) * 100)
                progress_bar.progress(percent,
                                      text=f"Analyzing {current}/{total}: {name}")

            with st.spinner("Analyzing student requirements..."):
                # Lazy import
                from logic.course_matching import generate_needs_matrix, \
                    compute_demand_summary

                # Generate needs matrix (uses cached bulk operations internally)
                needs_df = generate_needs_matrix(students_df,
                                                 progress_callback=update_progress)
                st.session_state["needs_df"] = needs_df

                # Compute demand summary ONCE here (cached)
                if not needs_df.empty:
                    # Create a hash for caching
                    df_hash = str(hash(needs_df.to_json()))
                    demand_df = compute_demand_summary(df_hash, needs_df)
                    st.session_state["demand_df"] = demand_df

            progress_bar.empty()
            save_current_session()  # Auto-save
            st.success("Needs Matrix Generated!")

    # Display results (no recomputation needed - just read from session_state)
    if "needs_df" in st.session_state and "demand_df" in st.session_state:
        demand_df = st.session_state["demand_df"].copy()

        st.divider()
        st.subheader("Course Demand & History")
        st.write(
            "All courses with at least 1 student demand are shown. Consider prioritizing high demand and courses not offered recently.")

        if not demand_df.empty:
            # Load requirements for course titles
            requirements_df = load_requirements()
            
            # Add formatted course display column
            demand_df["Course Display"] = demand_df["Course"].apply(
                lambda x: format_course_with_title(x, requirements_df)
            )
            
            sort_col = st.selectbox("Sort by", ["Demand", "Months Ago"], index=0)

            display_df = demand_df.sort_values(by=sort_col, ascending=False)

            # Show total count
            st.caption(f"Showing all {len(display_df)} courses with demand")

            # Reorder columns to show Course Display first
            column_order = ["Course Display", "Demand", "Last Offered", "Months Ago"]
            display_df = display_df[column_order]

            st.dataframe(
                display_df,
                use_container_width=True,
                height=min(len(display_df) * 35 + 38, 600),  # Dynamic height, max 600px
                column_config={
                    "Course Display": "Course",
                    "Last Offered": st.column_config.DateColumn("Last Offered"),
                    "Demand": st.column_config.ProgressColumn(
                        "Student Demand",
                        min_value=0,
                        max_value=max(demand_df["Demand"]) if len(demand_df) > 0 else 1,
                        format="%d",
                    ),
                },
            )
        else:
            st.info("No course needs identified.")

        with st.expander("View Full Needs Matrix (Students x Courses)"):
            st.dataframe(st.session_state["needs_df"])

        with st.expander("🔍 Debug: Course Demand Breakdown"):
            # Use a copy to avoid modifying the original
            debug_df = st.session_state["needs_df"].copy()
            metadata_cols = ["StudentId", "Name", "Email", "Major", "Cohort", "LastEnroll", "MajorPrefix"]
            course_cols = [c for c in debug_df.columns if c not in metadata_cols]

            st.write(f"**Total students in matrix:** {len(debug_df)}")
            st.write(f"**Total course columns:** {len(course_cols)}")

            # Count demand for ALL courses
            all_demands = []
            for course in course_cols:
                try:
                    count = int(debug_df[course].sum())
                    all_demands.append({"Course": course, "Demand": count})
                except (ValueError, TypeError):
                    pass  # Skip non-numeric columns

            all_demands_df = pd.DataFrame(all_demands).sort_values("Demand", ascending=True)

            # Show courses with zero demand
            zero_demand = all_demands_df[all_demands_df["Demand"] == 0]
            nonzero_demand = all_demands_df[all_demands_df["Demand"] > 0]

            st.write(f"**Courses with 0 demand (all students have taken):** {len(zero_demand)}")
            st.write(f"**Courses with >0 demand (showing in table above):** {len(nonzero_demand)}")

            if len(nonzero_demand) > 0:
                st.write(f"**Demand range:** {nonzero_demand['Demand'].min()} to {nonzero_demand['Demand'].max()}")

            st.write("**All courses sorted by demand (lowest first):**")
            st.dataframe(all_demands_df, use_container_width=True, height=300)

            # Major distribution (on copy, not original)
            st.write("**Student count by major prefix:**")
            debug_df["MajorPrefix"] = debug_df["Major"].apply(lambda x: x.split("-")[0] if "-" in str(x) else str(x)[:3])
            major_counts = debug_df["MajorPrefix"].value_counts()
            st.dataframe(major_counts, use_container_width=True)


def render_class_rosters_tab():
    """Class Rosters Tab."""
    st.subheader("Class Rosters")
    st.write("Create classes and assign students.")

    if "needs_df" not in st.session_state:
        st.warning("Please generate the Needs Matrix in the 'Match Courses' tab first.")
        return

    needs_df = st.session_state["needs_df"]

    # Initialize rosters in session state if not present
    if "rosters" not in st.session_state:
        st.session_state["rosters"] = {}

    # Get course options from demand list or needs matrix
    if "demand_df" in st.session_state and not st.session_state["demand_df"].empty:
        demand_df = st.session_state["demand_df"]
        course_options = demand_df.sort_values(by="Demand", ascending=False)[
            "Course"].tolist()
    else:
        metadata_cols = ["StudentId", "Name", "Email", "Major", "Cohort", "LastEnroll"]
        course_options = [c for c in needs_df.columns if c not in metadata_cols]

    # Load requirements for course title display
    requirements_df = load_requirements()
    
    selected_course = st.selectbox(
        "Select Course to Create/Manage",
        options=course_options,
        format_func=lambda x: format_course_with_title(x, requirements_df)
    )

    if selected_course:
        current_roster = st.session_state["rosters"].get(selected_course, [])
        st.info(
            f"Managing Roster for **{selected_course}** - Currently {len(current_roster)} students assigned.")

        # Filter Eligible Students
        eligible_students = needs_df[needs_df[selected_course] == 1].copy()
        
        # Extract major prefix for filtering (e.g., "TES-53E" -> "TES")
        eligible_students["MajorPrefix"] = eligible_students["Major"].apply(
            lambda x: x.split("-")[0] if "-" in str(x) else str(x)[:3]
        )

        # Filter by Major (applied first)
        st.write("**Filter by Major:**")
        selected_major = st.radio(
            "Select Major",
            options=["All", "BUS", "TES", "INT", "TOU", "FIN"],
            horizontal=True,
            label_visibility="collapsed"
        )
        
        if selected_major != "All":
            # Map display names to actual prefixes
            major_mapping = {
                "BUS": "BAD",  # Business Administration
                "TES": "TES",  # TESOL
                "INT": "INT",  # International Relations
                "TOU": "THM",  # Tourism and Hospitality Management
                "FIN": "FIN"   # Finance
            }
            actual_prefix = major_mapping.get(selected_major, selected_major)
            filtered_students = eligible_students[
                eligible_students["MajorPrefix"] == actual_prefix
            ]
        else:
            filtered_students = eligible_students
        
        # Filter by Cohort (applied second, after major filter)
        cohorts = sorted(filtered_students["Cohort"].unique().tolist())
        selected_cohort = st.selectbox("Filter by Cohort", ["All"] + cohorts)

        if selected_cohort != "All":
            filtered_students = filtered_students[
                filtered_students["Cohort"] == selected_cohort]

        # Display Interactive Table
        st.write("### Select Students to Assign")

        display_df = filtered_students[
            ["StudentId", "Name", "Major", "Cohort", "Email"]]

        event = st.dataframe(
            display_df,
            on_select="rerun",
            selection_mode="multi-row",
            use_container_width=True,
            hide_index=True,
        )

        # Assign Button
        if event.selection.rows:
            selected_indices = event.selection.rows
            selected_rows = display_df.iloc[selected_indices]

            if st.button(f"Assign {len(selected_rows)} Students to Roster"):
                new_students = []
                current_ids = [s["StudentId"] for s in current_roster]

                for _, row in selected_rows.iterrows():
                    student_entry = row.to_dict()
                    if student_entry["StudentId"] not in current_ids:
                        new_students.append(student_entry)

                st.session_state["rosters"][
                    selected_course] = current_roster + new_students
                save_current_session()  # Auto-save
                st.success(
                    f"Added {len(new_students)} students to {selected_course} roster!")
                st.rerun()

        # View Current Roster
        st.divider()
        st.write(f"### Current Roster for {selected_course} ({len(current_roster)})")

        if current_roster:
            roster_df = pd.DataFrame(current_roster)
            st.dataframe(roster_df, use_container_width=True, hide_index=True)

            col1, col2 = st.columns(2)
            with col1:
                if st.button("Clear Roster", type="secondary"):
                    st.session_state["rosters"][selected_course] = []
                    save_current_session()  # Auto-save
                    st.rerun()
            with col2:
                csv = roster_df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="Download Roster (CSV)",
                    data=csv,
                    file_name=f"roster_{selected_course}.csv",
                    mime="text/csv",
                )
        else:
            st.info("Roster is empty.")


def render_manage_rosters_tab():
    """Manage Rosters Tab - View all rosters and remove students."""
    st.subheader("Manage Rosters")
    st.write("View and edit all class rosters. Remove students as needed.")

    if "rosters" not in st.session_state or not st.session_state["rosters"]:
        st.warning("No rosters created yet. Go to 'Class Rosters' tab to create some.")
        return

    rosters = st.session_state["rosters"]
    active_rosters = {c: r for c, r in rosters.items() if len(r) > 0}

    if not active_rosters:
        st.info("All rosters are empty. Go to 'Class Rosters' tab to add students.")
        return

    # Get student course counts
    from logic.cache import get_student_course_counts
    student_counts = get_student_course_counts(rosters)

    # Summary stats
    total_assignments = sum(len(r) for r in active_rosters.values())
    unique_students = len(student_counts)
    over_enrolled = [s for s in student_counts.values() if s["count"] > 3]
    under_enrolled = [s for s in student_counts.values() if s["count"] < 3]

    st.info(f"**{len(active_rosters)}** classes | **{unique_students}** unique students | **{total_assignments}** total assignments")

    # Course limit filter section
    st.divider()
    st.subheader("📊 Student Course Load Analysis")
    st.write("Students should have exactly 3 courses per term.")

    filter_col1, filter_col2, filter_col3 = st.columns(3)

    with filter_col1:
        if over_enrolled:
            st.error(f"⚠️ **{len(over_enrolled)}** over-enrolled (>3 courses)")
        else:
            st.success("✅ No over-enrolled students")

    with filter_col2:
        if under_enrolled:
            st.warning(f"📉 **{len(under_enrolled)}** under-enrolled (<3 courses)")
        else:
            st.success("✅ No under-enrolled students")

    with filter_col3:
        correct_load = [s for s in student_counts.values() if s["count"] == 3]
        st.info(f"✅ **{len(correct_load)}** with exactly 3 courses")

    # Filter selector
    enrollment_filter = st.radio(
        "Filter students by enrollment status:",
        ["Show All Rosters", "Show Over-Enrolled (>3)", "Show Exactly 3 Courses (=3)", "Show Under-Enrolled (<3)"],
        horizontal=True,
        key="enrollment_filter"
    )

    # Display filtered students if a filter is selected
    if enrollment_filter == "Show Over-Enrolled (>3)":
        st.divider()
        st.subheader("⚠️ Over-Enrolled Students (>3 courses)")
        
        # Load requirements for course title display
        requirements_df = load_requirements()
        
        if over_enrolled:
            for student in sorted(over_enrolled, key=lambda x: x["count"], reverse=True):
                # Format course names with titles
                courses_display = [format_course_with_title(c, requirements_df) for c in student['courses']]
                
                with st.expander(f"🔴 {student['Name']} - {student['count']} courses", expanded=True):
                    st.write(f"**ID:** {student['StudentId']} | **Major:** {student['Major']} | **Cohort:** {student['Cohort']}")
                    st.write(f"**Enrolled in:** {', '.join(courses_display)}")

                    # Quick remove buttons
                    st.write("**Remove from:**")
                    cols = st.columns(min(len(student['courses']), 4))
                    for i, course in enumerate(student['courses']):
                        if cols[i % 4].button(f"🗑️ {course}", key=f"over_remove_{student['StudentId']}_{course}"):
                            remove_student_from_roster(course, student['StudentId'])
                            st.rerun()
        else:
            st.success("No over-enrolled students!")
        return  # Don't show regular roster view

    elif enrollment_filter == "Show Exactly 3 Courses (=3)":
        st.divider()
        st.subheader("✅ Students with Exactly 3 Courses")
        
        # Load requirements for course title display
        requirements_df = load_requirements()
        
        if correct_load:
            for student in sorted(correct_load, key=lambda x: x["Name"]):
                # Format course names with titles
                courses_display = [format_course_with_title(c, requirements_df) for c in student['courses']]
                
                with st.expander(f"🟢 {student['Name']} - {student['count']} courses", expanded=False):
                    st.write(f"**ID:** {student['StudentId']} | **Major:** {student['Major']} | **Cohort:** {student['Cohort']}")
                    st.write(f"**Enrolled in:** {', '.join(courses_display)}")

                    # Quick remove buttons (in case adjustment needed)
                    st.write("**Remove from:**")
                    cols = st.columns(min(len(student['courses']), 3))
                    for i, course in enumerate(student['courses']):
                        if cols[i].button(f"🗑️ {course}", key=f"correct_remove_{student['StudentId']}_{course}"):
                            remove_student_from_roster(course, student['StudentId'])
                            st.rerun()
        else:
            st.info("No students have exactly 3 courses yet.")
        return  # Don't show regular roster view

    elif enrollment_filter == "Show Under-Enrolled (<3)":
        st.divider()
        st.subheader("📉 Under-Enrolled Students (<3 courses)")
        
        # Load requirements for course title display
        requirements_df = load_requirements()
        
        if under_enrolled:
            # Get needs_df to calculate total remaining courses
            needs_df = st.session_state.get("needs_df")
            metadata_cols = ["StudentId", "Name", "Email", "Major", "Cohort", "LastEnroll", "MajorPrefix"]

            for student in sorted(under_enrolled, key=lambda x: x["count"]):
                # Calculate total courses left for this student
                courses_left = 0
                if needs_df is not None and not needs_df.empty:
                    student_row = needs_df[needs_df["StudentId"] == student["StudentId"]]
                    if not student_row.empty:
                        course_cols = [c for c in needs_df.columns if c not in metadata_cols]
                        for col in course_cols:
                            try:
                                if student_row[col].iloc[0] == 1:
                                    courses_left += 1
                            except (KeyError, IndexError, TypeError):
                                pass

                # Format course names with titles
                courses_display = [format_course_with_title(c, requirements_df) for c in student['courses']] if student['courses'] else []

                # Display with courses left info
                left_text = f" [{courses_left} left]" if courses_left > 0 else ""
                with st.expander(f"🟡 {student['Name']} - {student['count']} course(s){left_text}", expanded=False):
                    st.write(f"**ID:** {student['StudentId']} | **Major:** {student['Major']} | **Cohort:** {student['Cohort']}")
                    if courses_display:
                        st.write(f"**Currently enrolled in:** {', '.join(courses_display)}")
                    else:
                        st.write("**Currently enrolled in:** None")
                    st.write(f"**Total courses remaining to graduate:** {courses_left}")
                    st.caption("Go to 'Class Rosters' tab to add more courses for this student.")
        else:
            st.success("No under-enrolled students!")
        return  # Don't show regular roster view

    # Regular roster view (Show All Rosters)
    st.divider()
    st.subheader("📚 All Class Rosters")

    # Load requirements for course title display
    requirements_df = load_requirements()

    # Option to clear all rosters
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🗑️ Clear All Rosters", type="secondary"):
            st.session_state["rosters"] = {}
            save_current_session()  # Auto-save
            st.rerun()

    st.divider()

    # Show each roster in an expander
    for course, students in active_rosters.items():
        course_display = format_course_with_title(course, requirements_df)
        with st.expander(f"📚 {course_display} ({len(students)} students)", expanded=False):
            if students:
                # Create a dataframe with a remove column
                roster_df = pd.DataFrame(students)

                # Display the roster
                st.dataframe(
                    roster_df[["StudentId", "Name", "Major", "Cohort"]],
                    use_container_width=True,
                    hide_index=True,
                )

                # Remove individual students
                st.write("**Remove a student:**")
                cols = st.columns([3, 1])
                with cols[0]:
                    student_to_remove = st.selectbox(
                        "Select student",
                        options=[s["StudentId"] for s in students],
                        format_func=lambda x: f"{x} - {next((s['Name'] for s in students if s['StudentId'] == x), 'Unknown')}",
                        key=f"remove_select_{course}",
                        label_visibility="collapsed",
                    )
                with cols[1]:
                    if st.button("Remove", key=f"remove_btn_{course}", type="secondary"):
                        remove_student_from_roster(course, student_to_remove)
                        st.success(f"Removed student from {course}")
                        st.rerun()

                # Clear entire roster
                if st.button(f"Clear entire {course} roster", key=f"clear_{course}"):
                    st.session_state["rosters"][course] = []
                    save_current_session()  # Auto-save
                    st.rerun()

                # Download option
                csv = roster_df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label=f"Download {course} Roster (CSV)",
                    data=csv,
                    file_name=f"roster_{course}.csv",
                    mime="text/csv",
                    key=f"download_{course}",
                )


def render_schedule_optimization_tab():
    """Schedule Optimization Tab."""
    st.subheader("Optimize Schedule")
    st.write("Assign time slots to your created classes.")

    if "rosters" not in st.session_state or not st.session_state["rosters"]:
        st.warning("Please create classes in the 'Class Rosters' tab first.")
        return

    rosters = st.session_state["rosters"]
    active_classes = [c for c, r in rosters.items() if len(r) > 0]

    if not active_classes:
        st.info(
            "You haven't added any students to rosters yet. Go to 'Class Rosters' tab.")
        return

    st.write(f"You have created **{len(active_classes)}** active classes.")

    # Lazy import
    from logic.optimization import TIME_SLOTS, check_roster_conflicts
    
    # Load requirements for course title display
    requirements_df = load_requirements()

    offered_courses = {}

    # Create a grid layout for slot assignment
    cols = st.columns(3)
    for i, course in enumerate(active_classes):
        with cols[i % 3]:
            student_count = len(rosters.get(course, []))
            course_display = format_course_with_title(course, requirements_df)
            slot = st.selectbox(
                f"{course_display} ({student_count} students)",
                options=["Unassigned"] + TIME_SLOTS,
                key=f"slot_{course}",
            )
            if slot != "Unassigned":
                offered_courses[course] = slot

    st.divider()

    if st.button("Check Conflicts", type="primary"):
        conflicts = check_roster_conflicts(offered_courses, rosters)
        st.session_state["detected_conflicts"] = conflicts
        st.session_state["offered_courses"] = offered_courses

    # Display conflicts with resolution options
    if "detected_conflicts" in st.session_state:
        conflicts = st.session_state["detected_conflicts"]

        if conflicts:
            st.error(f"Found {len(conflicts)} student conflict(s)!")
            st.write("**Resolve conflicts by removing a student from one of their conflicting courses:**")

            for idx, conflict in enumerate(conflicts):
                # Format course names with titles
                courses_display = [format_course_with_title(c, requirements_df) for c in conflict['Courses']]
                
                with st.container():
                    st.markdown(f"""
                    ---
                    **Student:** {conflict['Name']} (`{conflict['StudentId']}`)
                    **Conflicting Slot:** `{conflict['ConflictSlot']}`
                    **Courses in conflict:** {', '.join(courses_display)}
                    """)

                    # Create remove buttons for each conflicting course
                    cols = st.columns(len(conflict['Courses']) + 1)
                    cols[0].write("Remove from:")

                    for i, course in enumerate(conflict['Courses']):
                        if cols[i + 1].button(
                            f"🗑️ {course}",
                            key=f"resolve_{conflict['StudentId']}_{course}_{idx}",
                            help=f"Remove {conflict['Name']} from {course}",
                        ):
                            remove_student_from_roster(course, conflict['StudentId'])
                            # Clear conflicts to force re-check
                            if "detected_conflicts" in st.session_state:
                                del st.session_state["detected_conflicts"]
                            st.success(f"Removed {conflict['Name']} from {course}. Click 'Check Conflicts' to verify.")
                            st.rerun()

            st.divider()
            st.info("💡 After resolving conflicts, click **Check Conflicts** again to verify.")

        else:
            st.success("✅ No conflicts found! This schedule looks good.")
            st.session_state["final_schedule"] = st.session_state.get("offered_courses", offered_courses)
            save_current_session()  # Auto-save

            # Show summary of the valid schedule
            if st.session_state.get("offered_courses"):
                st.write("**Final Schedule:**")
                schedule_data = [
                    {
                        "Course": format_course_with_title(c, requirements_df),
                        "Time Slot": s,
                        "Students": len(rosters.get(c, []))
                    }
                    for c, s in st.session_state["offered_courses"].items()
                ]
                st.dataframe(pd.DataFrame(schedule_data), use_container_width=True, hide_index=True)


def render_communications_tab():
    """Communications Tab."""
    st.subheader("Send Notifications")
    st.write("Email students and manage Telegram groups.")

    if "final_schedule" not in st.session_state or "needs_df" not in st.session_state:
        st.warning("Please optimize the schedule first.")
        return

    schedule = st.session_state["final_schedule"]
    needs_df = st.session_state["needs_df"]
    
    # Load requirements for course title display
    requirements_df = load_requirements()

    scheduled_courses = list(schedule.keys())

    # Identify affected students
    affected_students = []
    for _, row in needs_df.iterrows():
        student_courses = []
        for course in scheduled_courses:
            if course in row and row[course] == 1:
                student_courses.append(course)

        if student_courses:
            # Format courses with titles for display
            courses_display = [format_course_with_title(c, requirements_df) for c in student_courses]
            affected_students.append({
                "Name": row["Name"],
                "Email": row.get("Email", ""),
                "Courses": ", ".join(courses_display),
                "CoursesCodes": student_courses,  # Keep original codes for internal use
            })

    if not affected_students:
        st.warning("No students need the currently scheduled courses.")
        return

    st.info(f"Found {len(affected_students)} students to notify.")

    col1, col2 = st.columns(2)

    with col1:
        st.write("### Email Notifications")
        if st.button("Email All Scheduled Students"):
            from services.email_service import send_email

            progress_bar = st.progress(0)
            for i, student in enumerate(affected_students):
                email = student["Email"]
                if email:
                    subject = "Course Registration Update"
                    body = f"Dear {student['Name']},\n\nPlease register for the following courses: {student['Courses']}.\n\nBest,\nAcademic Office"
                    send_email(email, subject, body)
                progress_bar.progress((i + 1) / len(affected_students))

            st.success("Emails sent (check logs for mock output)!")

    with col2:
        st.write("### Telegram Notifications")
        telegram_chat_id = st.text_input(
            "Telegram Channel/Group ID",
            placeholder="@channel_name or -100xxxxx",
        )

        if st.button("Broadcast Update"):
            if telegram_chat_id:
                from services.telegram_bot import send_telegram_message

                message = "📢 **Course Schedule Update**\n\nThe following courses are now open for registration:\n\n"
                for course, slot in schedule.items():
                    course_display = format_course_with_title(course, requirements_df)
                    message += f"- {course_display}: {slot}\n"

                send_telegram_message(telegram_chat_id, message)
                st.success("Telegram update sent!")
            else:
                st.error("Please enter a Chat ID.")


def student_portal():
    st.header("Student Portal")
    st.write("Please log in to view your recommended schedule.")
    # Placeholder for student login and schedule view


if __name__ == "__main__":
    if check_login():
        main()
    else:
        login_page()
