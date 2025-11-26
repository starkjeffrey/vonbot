"""Integration tests for API endpoints.

These tests verify the complete request/response cycle for all API endpoints,
including authentication, validation, error handling, and database operations.
"""

from __future__ import annotations

import pytest
from fastapi import status


@pytest.mark.integration
class TestHealthEndpoint:
    """Test health check endpoint."""

    def test_health_check_success(self, client, mock_db_connection):
        """Test health check returns healthy status when DB is accessible."""
        # Configure mock to return successful query
        mock_cursor = mock_db_connection.cursor.return_value
        mock_cursor.fetchone.return_value = [1]

        response = client.get("/health")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"
        assert "timestamp" in data
        assert data["version"] == "1.0.0"

    def test_health_check_no_auth_required(self, client, mock_db_connection):
        """Test health check works without authentication."""
        mock_cursor = mock_db_connection.cursor.return_value
        mock_cursor.fetchone.return_value = [1]

        # No API key header
        response = client.get("/health")

        assert response.status_code == status.HTTP_200_OK

    def test_health_check_database_failure(self, client, mock_db_connection):
        """Test health check returns unhealthy when DB fails."""
        # Configure mock to raise exception
        mock_db_connection.cursor.side_effect = Exception("Connection refused")

        response = client.get("/health")

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["database"] == "disconnected"
        assert "error" in data


@pytest.mark.integration
class TestStudentCreation:
    """Test POST /students endpoint."""

    def test_create_student_success(
        self, client, auth_headers, mock_db_connection, sample_student_request
    ):
        """Test successful student creation."""
        # Configure mock to return no existing student, then successful insert
        mock_cursor = mock_db_connection.cursor.return_value
        mock_cursor.fetchone.side_effect = [
            None,  # Check for existing - not found
            [999],  # SELECT @@IDENTITY - return generated ID
        ]

        response = client.post(
            "/students", json=sample_student_request, headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["student_id"] == 12345
        assert data["legacy_student_id"] == 999
        assert "created" in data["message"].lower()

        # Verify database operations
        assert mock_cursor.execute.call_count == 3  # Check existing, insert, get ID
        assert mock_db_connection.commit.called
        assert mock_cursor.close.called

    def test_create_student_unauthenticated(self, client, sample_student_request):
        """Test student creation fails without API key."""
        response = client.post("/students", json=sample_student_request)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert "api key" in data["detail"].lower()

    def test_create_student_invalid_api_key(
        self, client, invalid_auth_headers, sample_student_request
    ):
        """Test student creation fails with invalid API key."""
        response = client.post(
            "/students", json=sample_student_request, headers=invalid_auth_headers
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_student_duplicate(
        self, client, auth_headers, mock_db_connection, sample_student_request
    ):
        """Test creating duplicate student returns 409 conflict."""
        # Configure mock to return existing student
        mock_cursor = mock_db_connection.cursor.return_value
        mock_cursor.fetchone.return_value = [999]  # Existing StudentID

        response = client.post(
            "/students", json=sample_student_request, headers=auth_headers
        )

        assert response.status_code == status.HTTP_409_CONFLICT
        data = response.json()
        assert "already exists" in data["detail"].lower()

        # Verify rollback not called (read-only check)
        assert not mock_db_connection.commit.called

    def test_create_student_validation_error(self, client, auth_headers):
        """Test invalid student data returns 422 validation error."""
        invalid_request = {
            "student_id": -1,  # Invalid: must be > 0
            "first_name": "",  # Invalid: min length 1
            "last_name": "Chan",
            "date_of_birth": "2000-01-15",
            "gender": "INVALID",  # Invalid: must be M, F, N, or X
        }

        response = client.post("/students", json=invalid_request, headers=auth_headers)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_student_missing_required_fields(self, client, auth_headers):
        """Test missing required fields returns validation error."""
        incomplete_request = {
            "student_id": 12345,
            # Missing: first_name, last_name, date_of_birth, gender
        }

        response = client.post(
            "/students", json=incomplete_request, headers=auth_headers
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_monk_student(
        self, client, auth_headers, mock_db_connection, sample_monk_request
    ):
        """Test creating monk student with is_monk=True."""
        mock_cursor = mock_db_connection.cursor.return_value
        mock_cursor.fetchone.side_effect = [None, [888]]

        response = client.post(
            "/students", json=sample_monk_request, headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["student_id"] == 67890

        # Verify Gender='Monk' was sent to database (check execute call)
        insert_call = mock_cursor.execute.call_args_list[1]  # Second execute (INSERT)
        insert_params = insert_call[0][1]  # Second argument is params tuple
        # Gender is at index 7 in INSERT params
        assert insert_params[7] == "Monk"

    def test_create_student_database_error(
        self, client, auth_headers, mock_db_connection, sample_student_request
    ):
        """Test database error returns 500."""
        # Configure mock to raise exception on execute
        mock_cursor = mock_db_connection.cursor.return_value
        mock_cursor.execute.side_effect = Exception("Database connection lost")

        response = client.post(
            "/students", json=sample_student_request, headers=auth_headers
        )

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert mock_db_connection.rollback.called


@pytest.mark.integration
class TestStudentRetrieval:
    """Test GET /students/{student_id} endpoint."""

    def test_get_student_success(
        self, client, auth_headers, mock_db_connection, sample_legacy_record
    ):
        """Test successful student retrieval."""
        # Configure mock to return student record
        mock_cursor = mock_db_connection.cursor.return_value
        mock_cursor.fetchone.return_value = sample_legacy_record

        response = client.get("/students/12345", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["StudentCode"] == 12345
        assert data["FirstName"] == "Sopheak"
        assert data["LastName"] == "Chan"
        assert data["Gender"] == "M"

    def test_get_student_not_found(self, client, auth_headers, mock_db_connection):
        """Test retrieving non-existent student returns None."""
        # Configure mock to return None
        mock_cursor = mock_db_connection.cursor.return_value
        mock_cursor.fetchone.return_value = None

        response = client.get("/students/99999", headers=auth_headers)

        # FastAPI returns None as null in JSON, which may result in 204 or null body
        # Depending on FastAPI version, this might be 200 with null or 204
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_204_NO_CONTENT]

    def test_get_student_unauthenticated(self, client):
        """Test get student fails without API key."""
        response = client.get("/students/12345")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_student_invalid_api_key(self, client, invalid_auth_headers):
        """Test get student fails with invalid API key."""
        response = client.get("/students/12345", headers=invalid_auth_headers)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_monk_student(
        self, client, auth_headers, mock_db_connection, sample_legacy_monk_record
    ):
        """Test retrieving monk student with Gender='Monk'."""
        mock_cursor = mock_db_connection.cursor.return_value
        mock_cursor.fetchone.return_value = sample_legacy_monk_record

        response = client.get("/students/67890", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["Gender"] == "Monk"
        assert data["IsMonk"] is True

    def test_get_student_database_error(self, client, auth_headers, mock_db_connection):
        """Test database error returns 500."""
        mock_cursor = mock_db_connection.cursor.return_value
        mock_cursor.execute.side_effect = Exception("Query timeout")

        response = client.get("/students/12345", headers=auth_headers)

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


@pytest.mark.integration
class TestStudentDeletion:
    """Test DELETE /students/{student_id} endpoint."""

    def test_delete_student_success(self, client, auth_headers, mock_db_connection):
        """Test successful student soft deletion."""
        # Configure mock to show 1 row updated
        mock_cursor = mock_db_connection.cursor.return_value
        mock_cursor.rowcount = 1

        response = client.delete("/students/12345", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert "inactive" in data["message"].lower()

        # Verify database operations
        assert mock_cursor.execute.called
        assert mock_db_connection.commit.called

    def test_delete_student_not_found(self, client, auth_headers, mock_db_connection):
        """Test deleting non-existent student returns 404."""
        # Configure mock to show 0 rows updated
        mock_cursor = mock_db_connection.cursor.return_value
        mock_cursor.rowcount = 0

        response = client.delete("/students/99999", headers=auth_headers)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_delete_student_unauthenticated(self, client):
        """Test delete student fails without API key."""
        response = client.delete("/students/12345")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_delete_student_invalid_api_key(self, client, invalid_auth_headers):
        """Test delete student fails with invalid API key."""
        response = client.delete("/students/12345", headers=invalid_auth_headers)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_delete_student_database_error(
        self, client, auth_headers, mock_db_connection
    ):
        """Test database error returns 500 and rolls back."""
        mock_cursor = mock_db_connection.cursor.return_value
        mock_cursor.execute.side_effect = Exception("Deadlock detected")

        response = client.delete("/students/12345", headers=auth_headers)

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert mock_db_connection.rollback.called


@pytest.mark.integration
@pytest.mark.security
class TestRateLimiting:
    """Test rate limiting middleware."""

    def test_rate_limit_enforcement(
        self, client, auth_headers, mock_db_connection, sample_student_request
    ):
        """Test rate limiting blocks excessive requests."""
        # Configure mock for successful operations
        mock_cursor = mock_db_connection.cursor.return_value
        mock_cursor.fetchone.side_effect = [None] + [[i] for i in range(100)]

        # Make requests up to limit (60 per minute by default)
        # First 60 should succeed
        for _i in range(60):
            response = client.post(
                "/students", json=sample_student_request, headers=auth_headers
            )
            assert response.status_code in [
                status.HTTP_200_OK,
                status.HTTP_409_CONFLICT,
            ]

        # 61st request should be rate limited
        response = client.post(
            "/students", json=sample_student_request, headers=auth_headers
        )
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

    def test_health_check_exempt_from_rate_limiting(self, client, mock_db_connection):
        """Test health check is not rate limited."""
        mock_cursor = mock_db_connection.cursor.return_value
        mock_cursor.fetchone.return_value = [1]

        # Make 100 health check requests (well over rate limit)
        for _ in range(100):
            response = client.get("/health")
            assert response.status_code == status.HTTP_200_OK


@pytest.mark.integration
@pytest.mark.security
class TestAuthentication:
    """Test API key authentication."""

    def test_missing_api_key(self, client, sample_student_request):
        """Test request without X-API-Key header is rejected."""
        response = client.post("/students", json=sample_student_request)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert "api key required" in data["detail"].lower()

    def test_invalid_api_key(self, client, sample_student_request):
        """Test request with wrong API key is rejected."""
        headers = {"X-API-Key": "wrong-key"}
        response = client.post(
            "/students", json=sample_student_request, headers=headers
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert "invalid" in data["detail"].lower()

    def test_valid_api_key(
        self, client, auth_headers, mock_db_connection, sample_student_request
    ):
        """Test request with correct API key is accepted."""
        mock_cursor = mock_db_connection.cursor.return_value
        mock_cursor.fetchone.side_effect = [None, [999]]

        response = client.post(
            "/students", json=sample_student_request, headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
