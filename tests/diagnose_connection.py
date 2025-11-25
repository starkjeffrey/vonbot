import os
import sys
import logging

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configure logging to print to console
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def diagnose():
    print("--- Diagnostic Start ---")
    print(f"Current Working Directory: {os.getcwd()}")
    
    freetds_env = os.environ.get("FREETDSCONF")
    print(f"FREETDSCONF env var: {freetds_env}")
    
    if freetds_env:
        if os.path.exists(freetds_env):
            print(f"✅ freetds.conf exists at {freetds_env}")
            with open(freetds_env, 'r') as f:
                print(f"--- Content of {freetds_env} ---")
                print(f.read())
                print("--------------------------------")
        else:
            print(f"❌ freetds.conf NOT found at {freetds_env}")
    else:
        print("⚠️ FREETDSCONF env var is NOT set.")

    print("\nAttempting to import database.connection...")
    try:
        from database.connection import get_db_connection, settings
        print("✅ Import successful.")
        print(f"Settings: Host={settings.LEGACY_DB_HOST}, Port={settings.LEGACY_DB_PORT}, User={settings.LEGACY_DB_USER}, DB={settings.LEGACY_DB_NAME}")
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return

    print("\nAttempting to connect...")
    try:
        conn = get_db_connection()
        print("✅ Connection successful!")
        
        cursor = conn.cursor()
        cursor.execute("SELECT @@VERSION")
        row = cursor.fetchone()
        print(f"Server Version: {row[0]}")
        
        conn.close()
        print("✅ Connection closed.")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        # Print detailed pymssql error if available
        if hasattr(e, 'args'):
            print(f"Error Args: {e.args}")

if __name__ == "__main__":
    diagnose()
