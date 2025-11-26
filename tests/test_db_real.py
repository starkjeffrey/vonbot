import pymssql
import os
from dotenv import load_dotenv

load_dotenv()


def test_connection():
    host = os.getenv("LEGACY_DB_HOST", "96.9.90.64")
    port = os.getenv("LEGACY_DB_PORT", "1500")
    user = os.getenv("LEGACY_DB_USER", "sa")
    password = os.getenv("LEGACY_DB_PASSWORD", "123456")
    dbname = os.getenv("LEGACY_DB_NAME", "New_PUCDB")

    # Point to local freetds.conf
    freetds_conf_path = os.path.abspath("freetds.conf")
    os.environ["FREETDSCONF"] = freetds_conf_path
    print(f"Using FREETDSCONF: {freetds_conf_path}")

    print(f"Attempting to connect to {host}:{port} as {user}...")

    try:
        conn = pymssql.connect(
            server=f"{host}:{port}",
            user=user,
            password=password,
            database=dbname,
            timeout=10,
            login_timeout=10,
            tds_version="7.3",
        )
        print("✅ Connection successful!")

        cursor = conn.cursor()
        cursor.execute("SELECT @@VERSION")
        row = cursor.fetchone()
        print(f"Server Version: {row[0]}")

        conn.close()
        return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False


if __name__ == "__main__":
    test_connection()
