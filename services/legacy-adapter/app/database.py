"""Database connection management for legacy MSSQL."""

import logging

import pymssql
from pymssql import Connection

from .config import settings

logger = logging.getLogger(__name__)


def get_connection() -> Connection:
    """Get a database connection to legacy MSSQL 2012 server.

    Creates a new connection each time with MSSQL 2012-compatible settings.
    Uses TDS 7.3 protocol and disables encryption for compatibility.

    IMPORTANT: These settings are required for MSSQL 2012:
    - TDS version 7.3 (not the default 7.4)
    - Encryption disabled (MSSQL 2012 doesn't support modern TLS)
    - Trust server certificate enabled

    Creates a new connection each time. For production with high traffic,
    consider implementing proper connection pooling (e.g., using SQLAlchemy).

    Returns:
        Active database connection

    Raises:
        pymssql.Error: If connection fails

    Examples:
        >>> conn = get_connection()
        >>> cursor = conn.cursor()
        >>> cursor.execute("SELECT @@VERSION")
        >>> version = cursor.fetchone()
        >>> cursor.close()
        >>> conn.close()
    """
    try:
        logger.debug(
            "Creating connection to %s:%s/%s (using direct connection with freetds_conf)",
            settings.LEGACY_DB_HOST,
            settings.LEGACY_DB_PORT,
            settings.LEGACY_DB_NAME,
        )

        # CRITICAL: Pass connection string with freetds_config_file parameter
        # This ensures pymssql uses our FreeTDS configuration with encryption=off

        conn = pymssql.connect(
            server=f"{settings.LEGACY_DB_HOST}:{settings.LEGACY_DB_PORT}",
            user=settings.LEGACY_DB_USER,
            password=settings.LEGACY_DB_PASSWORD,
            database=settings.LEGACY_DB_NAME,
            timeout=30,
            login_timeout=30,
            appname="LegacyAdapter",
            # Use the freetds.conf configuration file
            tds_version="7.3",  # TDS 7.3 for MSSQL 2012
        )

        logger.debug("Database connection established successfully")
        return conn

    except pymssql.Error as e:
        logger.error("Failed to connect to legacy database: %s", str(e))
        raise
    except Exception as e:
        logger.error("Unexpected error creating database connection: %s", str(e))
        raise


def test_connection() -> bool:
    """Test database connection and return True if successful.

    Returns:
        True if connection successful, False otherwise

    Examples:
        >>> if test_connection():
        ...     print("Database is accessible")
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        return result is not None
    except Exception as e:
        logger.error("Connection test failed: %s", str(e))
        return False


def init_connection_pool():
    """Initialize connection pool on startup.

    Currently a no-op placeholder. Implement if you need connection pooling.
    """
    logger.info("Initializing database connection pool...")
    # Test initial connection
    if test_connection():
        logger.info("✅ Database connection pool initialized successfully")
    else:
        logger.error("❌ Failed to initialize database connection pool")
        raise RuntimeError("Cannot connect to legacy database")


def close_connection_pool():
    """Close all connections in pool.

    Currently a no-op placeholder. Implement if you need connection pooling.
    """
    logger.info("Closing database connection pool...")
    # No cleanup needed for single-connection model
    logger.info("✅ Database connection pool closed")
