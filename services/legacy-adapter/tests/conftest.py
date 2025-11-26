"""Pytest configuration and shared fixtures for legacy-adapter tests.

This module provides test fixtures and configuration for testing the
legacy adapter service. It includes fixtures for:
- FastAPI test client
- Mock database connections
- Sample test data
- Authentication helpers
"""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from pymssql import Connection

if TYPE_CHECKING:
    from collections.abc import Generator

# Test configuration
TEST_API_KEY = "test-api-key-12345"
TEST_LEGACY_DB_HOST = "test-mssql-server"
TEST_LEGACY_DB_NAME = "test_legacy_db"


@pytest.fixture
def test_settings():
    """Override settings for testing."""
    with patch("app.config.settings") as mock_settings:
        mock_settings.API_KEY = TEST_API_KEY
        mock_settings.LEGACY_DB_HOST = TEST_LEGACY_DB_HOST
        mock_settings.LEGACY_DB_PORT = 1433
        mock_settings.LEGACY_DB_USER = "test_user"
        mock_settings.LEGACY_DB_PASSWORD = "test_password"
        mock_settings.LEGACY_DB_NAME = TEST_LEGACY_DB_NAME
        mock_settings.DEBUG = True
        mock_settings.LOG_LEVEL = "INFO"
        mock_settings.ALLOWED_ORIGINS = "http://localhost:8000"
        mock_settings.ALLOWED_HOSTS = "localhost"
        mock_settings.RATE_LIMIT_PER_MINUTE = 60
        mock_settings.API_HOST = "0.0.0.0"
        mock_settings.API_PORT = 8000
        yield mock_settings


@pytest.fixture
def mock_db_connection() -> Generator[MagicMock]:
    """Mock pymssql database connection."""
    mock_conn = MagicMock(spec=Connection)
    mock_cursor = MagicMock()

    # Configure cursor mock
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = None
    mock_cursor.fetchall.return_value = []
    mock_cursor.rowcount = 0
    mock_cursor.close.return_value = None
    mock_conn.close.return_value = None
    mock_conn.commit.return_value = None
    mock_conn.rollback.return_value = None

    yield mock_conn


@pytest.fixture
def client(test_settings, mock_db_connection) -> Generator[TestClient]:
    """FastAPI test client with mocked database.

    This fixture provides a test client with:
    - Mocked database connections
    - Test API key configured
    - Lifespan events disabled for faster tests
    """
    # Patch database connection before importing app
    with (
        patch("app.database.get_connection", return_value=mock_db_connection),
        patch("app.database.init_connection_pool"),
        patch("app.database.close_connection_pool"),
    ):
        from app.main import app

        with TestClient(app) as test_client:
            yield test_client


@pytest.fixture
def auth_headers() -> dict[str, str]:
    """Headers with valid API key for authenticated requests."""
    return {"X-API-Key": TEST_API_KEY}


@pytest.fixture
def invalid_auth_headers() -> dict[str, str]:
    """Headers with invalid API key for testing authentication."""
    return {"X-API-Key": "invalid-key"}


@pytest.fixture
def sample_student_request():
    """Sample student creation request matching Django schema."""
    return {
        "student_id": 12345,
        "first_name": "Sopheak",
        "last_name": "Chan",
        "middle_name": None,
        "english_first_name": "Sopheak",
        "english_last_name": "Chan",
        "date_of_birth": "2000-01-15",
        "gender": "M",
        "email": "sopheak.chan@example.com",
        "phone_number": "+85512345678",
        "is_monk": False,
        "preferred_study_time": "morning",
        "is_transfer_student": False,
        "status": "ACTIVE",
        "enrollment_date": "2024-01-10",
    }


@pytest.fixture
def sample_monk_request():
    """Sample student creation request for a monk."""
    return {
        "student_id": 67890,
        "first_name": "Bunthorn",
        "last_name": "Sao",
        "middle_name": None,
        "english_first_name": "Bunthorn",
        "english_last_name": "Sao",
        "date_of_birth": "1998-05-20",
        "gender": "M",
        "email": None,
        "phone_number": "+85598765432",
        "is_monk": True,
        "preferred_study_time": "morning",
        "is_transfer_student": False,
        "status": "ACTIVE",
        "enrollment_date": "2024-01-10",
    }


@pytest.fixture
def sample_legacy_record():
    """Sample student record from legacy MSSQL database."""
    return {
        "StudentID": 999,
        "StudentCode": 12345,
        "FirstName": "Sopheak",
        "LastName": "Chan",
        "MiddleName": None,
        "EnglishFirstName": "Sopheak",
        "EnglishLastName": "Chan",
        "DateOfBirth": date(2000, 1, 15),
        "Gender": "M",
        "Email": "sopheak.chan@example.com",
        "PhoneNumber": "+85512345678",
        "EnrollmentDate": date(2024, 1, 10),
        "Status": "Active",
        "IsMonk": False,
        "PreferredStudyTime": "Morning",
        "IsTransferStudent": False,
    }


@pytest.fixture
def sample_legacy_monk_record():
    """Sample monk record from legacy database (Gender='Monk')."""
    return {
        "StudentID": 888,
        "StudentCode": 67890,
        "FirstName": "Bunthorn",
        "LastName": "Sao",
        "MiddleName": None,
        "EnglishFirstName": "Bunthorn",
        "EnglishLastName": "Sao",
        "DateOfBirth": date(1998, 5, 20),
        "Gender": "Monk",  # Legacy uses "Monk" as gender value
        "Email": None,
        "PhoneNumber": "+85598765432",
        "EnrollmentDate": date(2024, 1, 10),
        "Status": "Active",
        "IsMonk": True,
        "PreferredStudyTime": "Morning",
        "IsTransferStudent": False,
    }


# Pytest configuration
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "unit: Unit tests (fast, no external dependencies)"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests (require mocked database)"
    )
    config.addinivalue_line("markers", "security: Security-focused tests")
    config.addinivalue_line(
        "markers", "contract: Contract tests for legacy schema compatibility"
    )
