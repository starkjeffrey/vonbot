from database.connection import db_cursor
import pandas as pd

def inspect_students():
    print("Inspecting Students schema...")
    query = "SELECT TOP 1 * FROM Students"
    
    try:
        with db_cursor() as cursor:
            cursor.execute(query)
            row = cursor.fetchone()
            if row:
                print("Columns in Students:", row.keys())
            else:
                print("Students table is empty.")
                
    except Exception as e:
        print(f"Error inspecting schema: {e}")

if __name__ == "__main__":
    inspect_students()
