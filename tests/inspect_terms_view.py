from database.connection import db_cursor


def inspect_data():
    print("--- Inspecting vw_BAlatestgrade Students ---")
    query = """
    SELECT TOP 10 s.ID, s.Name, s.BatchIDForMaster, v.termstart
    FROM vw_BAlatestgrade v
    JOIN Students s ON v.id = s.ID
    WHERE s.BatchIDForMaster IS NOT NULL AND s.BatchIDForMaster <> ''
    ORDER BY v.termstart DESC
    """
    try:
        with db_cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
            if rows:
                print(f"Found {len(rows)} students with Major data:")
                for row in rows:
                    print(row)
            else:
                print("No students in view have Major data!")
    except Exception as e:
        print(f"Error inspecting view students: {e}")


if __name__ == "__main__":
    inspect_data()
