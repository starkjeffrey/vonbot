"""Unit tests for audit logging system.

These tests verify the audit logging functionality, including:
- Event creation and serialization
- API key fingerprinting
- Structured JSON output
- Event type coverage
"""

from __future__ import annotations

import json
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from app.audit import (
    AuditEvent,
    AuditEventType,
    AuditLogger,
    AuditOutcome,
)


@pytest.mark.unit
class TestAuditEvent:
    """Test AuditEvent model."""

    def test_audit_event_creation(self):
        """Test creating basic audit event."""
        event = AuditEvent(
            event_id="20240130-120000-000001",
            event_type=AuditEventType.STUDENT_CREATED,
            api_key_fingerprint="abc123",
            client_ip="192.168.1.100",
            entity_type="student",
            entity_id=12345,
            operation="create",
            outcome=AuditOutcome.SUCCESS,
        )

        assert event.event_id == "20240130-120000-000001"
        assert event.event_type == AuditEventType.STUDENT_CREATED
        assert event.api_key_fingerprint == "abc123"
        assert event.client_ip == "192.168.1.100"
        assert event.entity_type == "student"
        assert event.entity_id == 12345
        assert event.outcome == AuditOutcome.SUCCESS

    def test_audit_event_to_json(self):
        """Test serializing audit event to JSON."""
        event = AuditEvent(
            event_id="test-001",
            event_type=AuditEventType.STUDENT_CREATED,
            timestamp=datetime(2024, 1, 30, 12, 0, 0),
            api_key_fingerprint="abc123",
            client_ip="192.168.1.100",
            entity_type="student",
            entity_id=12345,
            operation="create",
            outcome=AuditOutcome.SUCCESS,
            duration_ms=123.45,
            metadata={"legacy_student_id": 999},
        )

        json_str = event.to_json()
        data = json.loads(json_str)

        assert data["event_id"] == "test-001"
        assert data["event_type"] == "student.created"
        assert data["actor"]["api_key_fingerprint"] == "abc123"
        assert data["actor"]["client_ip"] == "192.168.1.100"
        assert data["operation"]["entity_type"] == "student"
        assert data["operation"]["entity_id"] == 12345
        assert data["outcome"]["status"] == "success"
        assert data["outcome"]["duration_ms"] == 123.45
        assert data["metadata"]["legacy_student_id"] == 999

    def test_audit_event_with_failure(self):
        """Test audit event with failure outcome."""
        event = AuditEvent(
            event_id="test-002",
            event_type=AuditEventType.AUTH_FAILURE,
            client_ip="192.168.1.200",
            operation="authenticate",
            outcome=AuditOutcome.FAILURE,
            outcome_reason="invalid_api_key",
        )

        assert event.outcome == AuditOutcome.FAILURE
        assert event.outcome_reason == "invalid_api_key"


@pytest.mark.unit
class TestAuditLogger:
    """Test AuditLogger class."""

    def test_generate_event_id(self):
        """Test event ID generation is unique and sequential."""
        logger = AuditLogger()

        id1 = logger._generate_event_id()
        id2 = logger._generate_event_id()

        assert id1 != id2
        # Both should have format: YYYYMMDD-HHMMSS-NNNNNN
        assert len(id1.split("-")) == 3
        assert len(id2.split("-")) == 3

    def test_fingerprint_api_key(self):
        """Test API key fingerprinting."""
        logger = AuditLogger()

        # Same key should produce same fingerprint
        key = "test-api-key-12345"
        fp1 = logger._fingerprint_api_key(key)
        fp2 = logger._fingerprint_api_key(key)

        assert fp1 == fp2
        assert len(fp1) == 16  # First 16 chars of SHA256

        # Different keys should produce different fingerprints
        different_key = "different-api-key"
        fp3 = logger._fingerprint_api_key(different_key)
        assert fp3 != fp1

    @patch("app.audit.logging.getLogger")
    def test_log_student_created_success(self, mock_get_logger):
        """Test logging successful student creation."""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        logger = AuditLogger()
        logger.logger = mock_logger

        logger.log_student_created(
            student_id=12345,
            legacy_student_id=999,
            api_key="test-key",
            client_ip="192.168.1.100",
            duration_ms=150.0,
            success=True,
        )

        # Verify logger.info was called
        assert mock_logger.info.called
        call_args = mock_logger.info.call_args[0][0]

        # Verify JSON structure
        data = json.loads(call_args)
        assert data["event_type"] == "student.created"
        assert data["operation"]["entity_id"] == 12345
        assert data["outcome"]["status"] == "success"
        assert data["metadata"]["legacy_student_id"] == 999

    @patch("app.audit.logging.getLogger")
    def test_log_student_created_failure(self, mock_get_logger):
        """Test logging failed student creation."""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        logger = AuditLogger()
        logger.logger = mock_logger

        logger.log_student_created(
            student_id=12345,
            legacy_student_id=None,
            api_key="test-key",
            client_ip="192.168.1.100",
            duration_ms=50.0,
            success=False,
            reason="duplicate_student_id",
        )

        call_args = mock_logger.info.call_args[0][0]
        data = json.loads(call_args)
        assert data["outcome"]["status"] == "failure"
        assert data["outcome"]["reason"] == "duplicate_student_id"

    @patch("app.audit.logging.getLogger")
    def test_log_student_read(self, mock_get_logger):
        """Test logging student read operation."""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        logger = AuditLogger()
        logger.logger = mock_logger

        logger.log_student_read(
            student_id=12345,
            api_key="test-key",
            client_ip="192.168.1.100",
            duration_ms=25.0,
            found=True,
        )

        call_args = mock_logger.info.call_args[0][0]
        data = json.loads(call_args)
        assert data["event_type"] == "student.read"
        assert data["operation"]["entity_id"] == 12345
        assert data["outcome"]["status"] == "success"

    @patch("app.audit.logging.getLogger")
    def test_log_student_read_not_found(self, mock_get_logger):
        """Test logging student read when not found."""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        logger = AuditLogger()
        logger.logger = mock_logger

        logger.log_student_read(
            student_id=99999,
            api_key="test-key",
            client_ip="192.168.1.100",
            found=False,
        )

        call_args = mock_logger.info.call_args[0][0]
        data = json.loads(call_args)
        assert data["outcome"]["status"] == "failure"
        assert data["outcome"]["reason"] == "not_found"

    @patch("app.audit.logging.getLogger")
    def test_log_student_deleted(self, mock_get_logger):
        """Test logging student deletion."""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        logger = AuditLogger()
        logger.logger = mock_logger

        logger.log_student_deleted(
            student_id=12345,
            api_key="test-key",
            client_ip="192.168.1.100",
            duration_ms=75.0,
            success=True,
        )

        call_args = mock_logger.info.call_args[0][0]
        data = json.loads(call_args)
        assert data["event_type"] == "student.deleted"
        assert data["operation"]["action"] == "soft_delete"
        assert data["outcome"]["status"] == "success"

    @patch("app.audit.logging.getLogger")
    def test_log_auth_failure(self, mock_get_logger):
        """Test logging authentication failure."""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        logger = AuditLogger()
        logger.logger = mock_logger

        logger.log_auth_failure(
            api_key_provided="wrong-key",
            client_ip="192.168.1.200",
            reason="invalid_api_key",
        )

        call_args = mock_logger.info.call_args[0][0]
        data = json.loads(call_args)
        assert data["event_type"] == "auth.failure"
        assert data["outcome"]["status"] == "failure"
        assert data["outcome"]["reason"] == "invalid_api_key"

    @patch("app.audit.logging.getLogger")
    def test_log_auth_failure_missing_key(self, mock_get_logger):
        """Test logging auth failure when API key is missing."""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        logger = AuditLogger()
        logger.logger = mock_logger

        logger.log_auth_failure(
            api_key_provided=None,
            client_ip="192.168.1.200",
            reason="missing_api_key",
        )

        call_args = mock_logger.info.call_args[0][0]
        data = json.loads(call_args)
        assert data["actor"]["api_key_fingerprint"] is None
        assert data["outcome"]["reason"] == "missing_api_key"

    @patch("app.audit.logging.getLogger")
    def test_log_rate_limit_exceeded(self, mock_get_logger):
        """Test logging rate limit violation."""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        logger = AuditLogger()
        logger.logger = mock_logger

        logger.log_rate_limit_exceeded(
            client_ip="192.168.1.200",
            api_key="test-key",
            endpoint="/students",
        )

        call_args = mock_logger.info.call_args[0][0]
        data = json.loads(call_args)
        assert data["event_type"] == "rate_limit.exceeded"
        assert data["metadata"]["endpoint"] == "/students"

    @patch("app.audit.logging.getLogger")
    def test_log_database_error(self, mock_get_logger):
        """Test logging database error."""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        logger = AuditLogger()
        logger.logger = mock_logger

        logger.log_database_error(
            operation="create_student",
            error_message="Connection timeout",
            entity_type="student",
            entity_id=12345,
            api_key="test-key",
            client_ip="192.168.1.100",
        )

        call_args = mock_logger.info.call_args[0][0]
        data = json.loads(call_args)
        assert data["event_type"] == "error.database"
        assert data["outcome"]["reason"] == "Connection timeout"
        assert data["operation"]["entity_type"] == "student"


@pytest.mark.unit
class TestAuditEventTypes:
    """Test all audit event types are covered."""

    def test_all_event_types_defined(self):
        """Test that all expected event types are defined."""
        expected_events = [
            "STUDENT_CREATED",
            "STUDENT_READ",
            "STUDENT_UPDATED",
            "STUDENT_DELETED",
            "AUTH_SUCCESS",
            "AUTH_FAILURE",
            "AUTH_MISSING",
            "RATE_LIMIT_EXCEEDED",
            "HEALTH_CHECK",
            "SERVICE_STARTED",
            "SERVICE_STOPPED",
            "DATABASE_ERROR",
            "VALIDATION_ERROR",
            "INTERNAL_ERROR",
        ]

        for event_name in expected_events:
            assert hasattr(AuditEventType, event_name), (
                f"Missing event type: {event_name}"
            )

    def test_outcome_types(self):
        """Test that all outcome types are defined."""
        assert hasattr(AuditOutcome, "SUCCESS")
        assert hasattr(AuditOutcome, "FAILURE")
        assert hasattr(AuditOutcome, "PARTIAL")
