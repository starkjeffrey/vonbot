import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Academic Scheduling Tool",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)


def check_db_status():
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
        st.header("Navigation")
        app_mode = st.radio("Go to", ["Admin Dashboard", "Student Portal"])

        st.divider()
        st.header("System Status")

        is_connected, error_msg = check_db_status()
        if is_connected:
            st.write("Database: 🟢 Connected")
        else:
            st.write("Database: 🔴 Disconnected")
            if error_msg:
                st.error(f"Error: {error_msg}")

    if app_mode == "Admin Dashboard":
        admin_dashboard()
    elif app_mode == "Student Portal":
        student_portal()


def admin_dashboard():
    st.header("Admin Dashboard")

    tabs = st.tabs(
        [
            "Student Selection",
            "Course Matching",
            "Class Rosters",
            "Schedule Optimization",
            "Communications",
        ]
    )

    with tabs[0]:
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
                    from logic.student_selection import get_active_students

                    students_df = get_active_students(months_option)
                    st.session_state["students_df"] = students_df
                    st.success(f"Found {len(students_df)} active students.")

            # Select a student to view requirements
            if (
                "students_df" in st.session_state
                and not st.session_state["students_df"].empty
            ):
                students_df = st.session_state["students_df"]
                st.selectbox(
                    "Select Student to View Requirements",
                    options=students_df["StudentId"].tolist(),
                    format_func=lambda x: f"{x} - {students_df[students_df['StudentId'] == x].iloc[0]['Name']}",
                )
            else:
                st.info("Fetch students first to select one.")

        with col2:
            if (
                "students_df" in st.session_state
                and not st.session_state["students_df"].empty
            ):
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

    with tabs[1]:
        st.subheader("Match Courses")
        st.write("Match students to required courses.")

        if (
            "students_df" in st.session_state
            and not st.session_state["students_df"].empty
        ):
            students_df = st.session_state["students_df"]

            col1, col2 = st.columns([1, 1])

            with col1:
                if st.button("Generate Needs Matrix", type="primary"):
                    # Create a placeholder for progress
                    progress_bar = st.progress(0, text="Starting analysis...")
                    status_text = st.empty()

                    def update_progress(current, total, name):
                        percent = int((current / total) * 100)
                        progress_bar.progress(
                            percent, text=f"Analyzing {current}/{total}: {name}"
                        )

                    with st.spinner("Analyzing student requirements..."):
                        from logic.course_matching import (
                            generate_needs_matrix,
                            get_course_last_offered,
                        )

                        needs_df = generate_needs_matrix(
                            students_df, progress_callback=update_progress
                        )
                        st.session_state["needs_df"] = needs_df

                    progress_bar.empty()
                    status_text.empty()
                    st.success("Needs Matrix Generated!")

            if "needs_df" in st.session_state:
                needs_df = st.session_state["needs_df"]

                # Calculate Course Demand Summary
                metadata_cols = ["StudentId", "Name", "Major", "Cohort", "LastEnroll"]
                course_cols = [c for c in needs_df.columns if c not in metadata_cols]

                demand_data = []
                for course in course_cols:
                    count = needs_df[course].sum()
                    if count > 0:
                        # Fetch history
                        from logic.course_matching import get_course_last_offered

                        history = get_course_last_offered(course)
                        last_offered = history["StartDate"] if history else None
                        months_ago = (
                            history["MonthsAgo"] if history else 999
                        )  # Never offered?

                        demand_data.append(
                            {
                                "Course": course,
                                "Demand": int(count),
                                "Last Offered": last_offered,
                                "Months Ago": months_ago,
                            }
                        )

                demand_df = pd.DataFrame(demand_data)
                st.session_state["demand_df"] = demand_df  # Save for other tabs

                st.divider()
                st.subheader("Course Demand & History")
                st.write(
                    "Prioritize courses with high demand (>16) and long time since last offered."
                )

                if not demand_df.empty:
                    # Allow sorting
                    sort_col = st.selectbox(
                        "Sort by", ["Demand", "Months Ago"], index=0
                    )
                    ascending = False

                    demand_df = demand_df.sort_values(by=sort_col, ascending=ascending)

                    st.dataframe(
                        demand_df,
                        use_container_width=True,
                        column_config={
                            "Last Offered": st.column_config.DateColumn("Last Offered"),
                            "Demand": st.column_config.ProgressColumn(
                                "Student Demand",
                                min_value=0,
                                max_value=max(demand_df["Demand"]),
                                format="%d",
                            ),
                        },
                    )
                else:
                    st.info("No course needs identified.")

                with st.expander("View Full Needs Matrix (Students x Courses)"):
                    st.dataframe(needs_df)

        else:
            st.warning("Please fetch students in the 'Student Selection' tab first.")

    with tabs[2]:
        st.subheader("Class Rosters")
        st.write("Create classes and assign students.")

        if "needs_df" in st.session_state:
            needs_df = st.session_state["needs_df"]

            # Initialize rosters in session state if not present
            if "rosters" not in st.session_state:
                st.session_state["rosters"] = {}

            # Select Course to Create/Manage from Demand List
            if "demand_df" in st.session_state:
                demand_df = st.session_state["demand_df"]
                # Sort by demand for easier selection
                course_options = demand_df.sort_values(by="Demand", ascending=False)[
                    "Course"
                ].tolist()
            else:
                metadata_cols = ["StudentId", "Name", "Major", "Cohort", "LastEnroll"]
                course_options = [c for c in needs_df.columns if c not in metadata_cols]

            selected_course = st.selectbox(
                "Select Course to Create/Manage", options=course_options
            )

            if selected_course:
                current_roster = st.session_state["rosters"].get(selected_course, [])
                st.info(
                    f"Managing Roster for **{selected_course}** - Currently {len(current_roster)} students assigned."
                )

                # Filter Eligible Students (Need the course AND not already in roster)
                eligible_students = needs_df[needs_df[selected_course] == 1].copy()

                # Filter by Cohort
                cohorts = sorted(eligible_students["Cohort"].unique().tolist())
                selected_cohort = st.selectbox("Filter by Cohort", ["All"] + cohorts)

                if selected_cohort != "All":
                    filtered_students = eligible_students[
                        eligible_students["Cohort"] == selected_cohort
                    ]
                else:
                    filtered_students = eligible_students

                # Display Interactive Table
                st.write("### Select Students to Assign")
                st.write("Highlight rows to select students.")

                display_df = filtered_students[
                    ["StudentId", "Name", "Major", "Cohort", "Email"]
                ]

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
                        # Add new students (avoid duplicates)
                        new_students = []
                        current_ids = [s["StudentId"] for s in current_roster]

                        for _, row in selected_rows.iterrows():
                            student_entry = row.to_dict()
                            if student_entry["StudentId"] not in current_ids:
                                new_students.append(student_entry)

                        st.session_state["rosters"][selected_course] = (
                            current_roster + new_students
                        )
                        st.success(
                            f"Added {len(new_students)} students to {selected_course} roster!"
                        )
                        st.rerun()

                # View Current Roster
                st.divider()
                st.write(
                    f"### Current Roster for {selected_course} ({len(current_roster)})"
                )

                if current_roster:
                    roster_df = pd.DataFrame(current_roster)
                    st.dataframe(roster_df, use_container_width=True, hide_index=True)

                    # Remove Button (Optional - could add later)
                    if st.button("Clear Roster", type="secondary"):
                        st.session_state["rosters"][selected_course] = []
                        st.rerun()

                    # Export Button
                    csv = roster_df.to_csv(index=False).encode("utf-8")
                    st.download_button(
                        label="Download Roster (CSV)",
                        data=csv,
                        file_name=f"roster_{selected_course}.csv",
                        mime="text/csv",
                    )
                else:
                    st.info("Roster is empty.")

        else:
            st.warning(
                "Please generate the Needs Matrix in the 'Match Courses' tab first."
            )

    with tabs[3]:
        st.subheader("Optimize Schedule")
        st.write("Assign time slots to your created classes.")

        if "rosters" in st.session_state and st.session_state["rosters"]:
            rosters = st.session_state["rosters"]
            # Only show courses that have at least one student assigned
            active_classes = [c for c, r in rosters.items() if len(r) > 0]

            if active_classes:
                st.write(f"You have created **{len(active_classes)}** active classes.")

                from logic.optimization import TIME_SLOTS, check_roster_conflicts

                # Dictionary to store assigned slots
                offered_courses = {}

                # Create a grid layout for slot assignment
                cols = st.columns(3)
                for i, course in enumerate(active_classes):
                    with cols[i % 3]:
                        slot = st.selectbox(
                            f"Slot for {course}",
                            options=["Unassigned"] + TIME_SLOTS,
                            key=f"slot_{course}",
                        )
                        if slot != "Unassigned":
                            offered_courses[course] = slot

                st.divider()

                if st.button("Check Conflicts", type="primary"):
                    conflicts = check_roster_conflicts(offered_courses, rosters)

                    if conflicts:
                        st.error(f"Found {len(conflicts)} student conflicts!")

                        conflict_df = pd.DataFrame(conflicts)
                        st.dataframe(
                            conflict_df,
                            column_config={"Courses": "Conflicting Courses"},
                            use_container_width=True,
                        )
                    else:
                        st.success("No conflicts found! This schedule looks good.")

                        # Save schedule to session state for next step
                        st.session_state["final_schedule"] = offered_courses
            else:
                st.info(
                    "You haven't added any students to rosters yet. Go to 'Class Rosters' tab."
                )

        else:
            st.warning("Please create classes in the 'Class Rosters' tab first.")

    with tabs[4]:
        st.subheader("Send Notifications")
        st.write("Email students and manage Telegram groups.")

        if "final_schedule" in st.session_state and "needs_df" in st.session_state:
            schedule = st.session_state["final_schedule"]
            needs_df = st.session_state["needs_df"]

            # Filter students who need the scheduled courses
            scheduled_courses = list(schedule.keys())

            # Identify affected students
            affected_students = []
            for _, row in needs_df.iterrows():
                student_courses = []
                for course in scheduled_courses:
                    if course in row and row[course] == 1:
                        student_courses.append(course)

                if student_courses:
                    affected_students.append(
                        {
                            "Name": row["Name"],
                            "Email": row.get("Email", ""),
                            "Courses": ", ".join(student_courses),
                        }
                    )

            if affected_students:
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
                                message += f"- {course}: {slot}\n"

                            send_telegram_message(telegram_chat_id, message)
                            st.success("Telegram update sent!")
                        else:
                            st.error("Please enter a Chat ID.")
            else:
                st.warning("No students need the currently scheduled courses.")
        else:
            st.warning("Please optimize the schedule first.")


def student_portal():
    st.header("Student Portal")
    st.write("Please log in to view your recommended schedule.")
    # Placeholder for student login and schedule view


if __name__ == "__main__":
    main()
