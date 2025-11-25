import logging
import pymssql
import os
from contextlib import contextmanager
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configure FreeTDS to use local config (Critical for MSSQL 2008/2012)
freetds_conf_path = os.path.abspath("freetds.conf")
if os.path.exists(freetds_conf_path):
    os.environ["FREETDSCONF"] = freetds_conf_path
    logger.info(f"Using FREETDSCONF: {freetds_conf_path}")

# Settings class to handle configuration
class Settings:
    LEGACY_DB_HOST = os.getenv("LEGACY_DB_HOST", "96.9.90.64")
    LEGACY_DB_PORT = int(os.getenv("LEGACY_DB_PORT", 1500))
    LEGACY_DB_USER = os.getenv("LEGACY_DB_USER", "sa")
    LEGACY_DB_PASSWORD = os.getenv("LEGACY_DB_PASSWORD", "123456")
    LEGACY_DB_NAME = os.getenv("LEGACY_DB_NAME", "New_PUCDB")

settings = Settings()

def get_db_connection():
    """
    Get a database connection to legacy MSSQL 2012 server.
    Uses settings compatible with MSSQL 2012 (TDS 7.3, no encryption).
    """
    try:
        logger.debug(f"Connecting to {settings.LEGACY_DB_HOST}:{settings.LEGACY_DB_PORT}")
        conn = pymssql.connect(
            server=f"{settings.LEGACY_DB_HOST}:{settings.LEGACY_DB_PORT}",
            user=settings.LEGACY_DB_USER,
            password=settings.LEGACY_DB_PASSWORD,
            database=settings.LEGACY_DB_NAME,
            timeout=30,
            login_timeout=30,
            appname="AcademicSchedulingTool",
            tds_version="7.3",  # Critical for MSSQL 2012
            # encryption is handled by freetds.conf or default lib behavior with tds_version
        )
        return conn
    except pymssql.Error as e:
        logger.error(f"Database connection failed: {e}")
        raise

@contextmanager
def db_cursor():
    """Context manager for database cursor."""
    conn = None
    try:
        conn = get_db_connection()
        yield conn.cursor(as_dict=True)
    except Exception as e:
        logger.error(f"Database error: {e}")
        raise
    finally:
        if conn:
            conn.close()
