import pandas as pd
from database.connection import db_cursor

def get_active_students(months_back: int = 6):
    """
    Fetch students who have been active in the last X months.
    
    Args:
        months_back (int): Number of months to look back for activity.
        
    Returns:
        pd.DataFrame: DataFrame of active students.
    """
    query = f"""
    SELECT DISTINCT 
        s.ID as StudentId, 
        s.Name,
        s.schoolemail as Email,
        s.BatchIDForMaster as MajorCode,
        SUBSTRING(s.BatchIDForMaster, 5, 3) as Cohort,
        MAX(v.termstart) as LastActiveDate
    FROM vw_BAlatestgrade v
    JOIN Students s ON v.id = s.ID
    WHERE v.termstart >= CONVERT(varchar, DATEADD(month, -%d, GETDATE()), 111)
    AND s.BatchIDForMaster IS NOT NULL 
    AND s.BatchIDForMaster <> ''
    GROUP BY s.ID, s.Name, s.schoolemail, s.BatchIDForMaster, SUBSTRING(s.BatchIDForMaster, 5, 3)
    ORDER BY LastActiveDate DESC
    """
    
    try:
        with db_cursor() as cursor:
            cursor.execute(query % months_back)
            data = cursor.fetchall()
            
            if not data:
                return pd.DataFrame(columns=["StudentId", "Name", "MajorCode", "Cohort", "LastActiveDate"])
                
            df = pd.DataFrame(data)
            return df
            
    except Exception as e:
        print(f"Error fetching students: {e}")
        return pd.DataFrame(columns=["StudentId", "Name", "MajorCode", "Cohort", "LastActiveDate"])
