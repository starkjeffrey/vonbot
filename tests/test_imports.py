import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def test_imports():
    try:
        import app
        import database.connection
        import database.local_db
        import logic.student_selection
        import logic.course_matching
        import logic.optimization
        import services.telegram_bot
        import services.email_service
        import models.data_models

        print("✅ All modules imported successfully.")
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    test_imports()
