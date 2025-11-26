import sqlite3
import logging

logger = logging.getLogger(__name__)

DB_PATH = "admin_session.db"


def init_local_db():
    """Initialize the local SQLite database for admin session data."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Table for storing temporary student lists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS session_students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT,
                name TEXT,
                major TEXT,
                selected BOOLEAN DEFAULT 1
            )
        """)

        # Table for storing course recommendations
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS course_recommendations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT,
                course_id TEXT,
                course_name TEXT,
                priority INTEGER,
                status TEXT DEFAULT 'pending'
            )
        """)

        conn.commit()
        conn.close()
        logger.info("Local database initialized.")
    except Exception as e:
        logger.error(f"Failed to initialize local DB: {e}")


def get_local_connection():
    return sqlite3.connect(DB_PATH)
