"""Audit logging system for legacy adapter operations.

This module provides structured audit logging for compliance and security monitoring.
All operations that modify or access legacy database records are audited with:
- Event type (created, updated, deleted, accessed, failed)
- Actor context (API key fingerprint, IP address)
- Temporal context (timestamp, duration)
- Operation details (entity type, entity ID, changes)
- Outcome (success/failure with reason)

Audit logs are written as structured JSON for easy parsing and analysis.
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger("audit")


class AuditEventType(str, Enum):
    """Types of auditable events."""

    # Student operations
    STUDENT_CREATED = "student.created"
    STUDENT_READ = "student.read"
    STUDENT_UPDATED = "student.updated"
    STUDENT_DELETED = "student.deleted"

    # Authentication events
    AUTH_SUCCESS = "auth.success"
    AUTH_FAILURE = "auth.failure"
    AUTH_MISSING = "auth.missing"

    # Rate limiting events
    RATE_LIMIT_EXCEEDED = "rate_limit.exceeded"

    # System events
    HEALTH_CHECK = "system.health_check"
    SERVICE_STARTED = "system.started"
    SERVICE_STOPPED = "system.stopped"

    # Error events
    DATABASE_ERROR = "error.database"
    VALIDATION_ERROR = "error.validation"
    INTERNAL_ERROR = "error.internal"


class AuditOutcome(str, Enum):
    """Outcome of audited operation."""

    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"  # Operation partially completed


class AuditEvent(BaseModel):
    """Structured audit event record.

    This model captures all relevant information about an audited operation
    for compliance, security monitoring, and troubleshooting.
    """

    # Event identification
    event_id: str = Field(..., description="Unique event identifier (UUID)")
    event_type: AuditEventType = Field(..., description="Type of event")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="UTC timestamp")

    # Actor context (who)
    api_key_fingerprint: str | None = Field(None, description="SHA256 fingerprint of API key (first 16 chars)")
    client_ip: str | None = Field(None, description="Client IP address")
    user_agent: str | None = Field(None, description="HTTP User-Agent header")

    # Operation context (what)
    entity_type: str | None = Field(None, description="Type of entity (student, course, etc.)")
    entity_id: int | None = Field(None, description="ID of affected entity")
    operation: str | None = Field(None, description="Operation performed (create, read, update, delete)")

    # Outcome context (result)
    outcome: AuditOutcome = Field(..., description="Operation outcome")
    outcome_reason: str | None = Field(None, description="Reason for failure or additional context")

    # Performance context
    duration_ms: float | None = Field(None, description="Operation duration in milliseconds")

    # Additional context
    metadata: dict[str, Any] | None = Field(None, description="Additional event-specific data")

    def to_json(self) -> str:
        """Serialize audit event to JSON string.

        Returns:
            JSON string representation of audit event
        """
        return json.dumps(
            {
                "event_id": self.event_id,
                "event_type": self.event_type.value,
                "timestamp": self.timestamp.isoformat(),
                "actor": {
                    "api_key_fingerprint": self.api_key_fingerprint,
                    "client_ip": self.client_ip,
                    "user_agent": self.user_agent,
                },
                "operation": {
                    "entity_type": self.entity_type,
                    "entity_id": self.entity_id,
                    "action": self.operation,
                },
                "outcome": {
                    "status": self.outcome.value,
                    "reason": self.outcome_reason,
                    "duration_ms": self.duration_ms,
                },
                "metadata": self.metadata or {},
            },
            default=str,  # Handle any non-serializable types
        )


class AuditLogger:
    """Centralized audit logging system.

    This class provides methods for logging various types of audit events
    with consistent structure and formatting.
    """

    def __init__(self):
        """Initialize audit logger."""
        self.logger = logging.getLogger("audit")
        self._request_counter = 0

    def _generate_event_id(self) -> str:
        """Generate unique event ID.

        Returns:
            Event ID in format: YYYYMMDD-HHMMSS-COUNTER
        """
        self._request_counter += 1
        now = datetime.utcnow()
        return f"{now.strftime('%Y%m%d-%H%M%S')}-{self._request_counter:06d}"

    def _fingerprint_api_key(self, api_key: str) -> str:
        """Create SHA256 fingerprint of API key.

        Args:
            api_key: Full API key

        Returns:
            First 16 characters of SHA256 hash
        """
        hash_obj = hashlib.sha256(api_key.encode())
        return hash_obj.hexdigest()[:16]

    def log_event(self, event: AuditEvent) -> None:
        """Log audit event to structured log.

        Args:
            event: Audit event to log
        """
        self.logger.info(event.to_json())

    def log_student_created(
        self,
        student_id: int,
        legacy_student_id: int | None,
        api_key: str | None = None,
        client_ip: str | None = None,
        duration_ms: float | None = None,
        success: bool = True,
        reason: str | None = None,
    ) -> None:
        """Log student creation event.

        Args:
            student_id: Django-generated student ID
            legacy_student_id: Legacy database primary key
            api_key: API key used for authentication
            client_ip: Client IP address
            duration_ms: Operation duration
            success: Whether operation succeeded
            reason: Failure reason if applicable
        """
        event = AuditEvent(
            event_id=self._generate_event_id(),
            event_type=AuditEventType.STUDENT_CREATED,
            api_key_fingerprint=self._fingerprint_api_key(api_key) if api_key else None,
            client_ip=client_ip,
            entity_type="student",
            entity_id=student_id,
            operation="create",
            outcome=AuditOutcome.SUCCESS if success else AuditOutcome.FAILURE,
            outcome_reason=reason,
            duration_ms=duration_ms,
            metadata={"legacy_student_id": legacy_student_id} if legacy_student_id else None,
        )
        self.log_event(event)

    def log_student_read(
        self,
        student_id: int,
        api_key: str | None = None,
        client_ip: str | None = None,
        duration_ms: float | None = None,
        found: bool = True,
    ) -> None:
        """Log student retrieval event.

        Args:
            student_id: Student ID being retrieved
            api_key: API key used
            client_ip: Client IP
            duration_ms: Query duration
            found: Whether student was found
        """
        event = AuditEvent(
            event_id=self._generate_event_id(),
            event_type=AuditEventType.STUDENT_READ,
            api_key_fingerprint=self._fingerprint_api_key(api_key) if api_key else None,
            client_ip=client_ip,
            entity_type="student",
            entity_id=student_id,
            operation="read",
            outcome=AuditOutcome.SUCCESS if found else AuditOutcome.FAILURE,
            outcome_reason="not_found" if not found else None,
            duration_ms=duration_ms,
        )
        self.log_event(event)

    def log_student_deleted(
        self,
        student_id: int,
        api_key: str | None = None,
        client_ip: str | None = None,
        duration_ms: float | None = None,
        success: bool = True,
        reason: str | None = None,
    ) -> None:
        """Log student deletion (soft delete) event.

        Args:
            student_id: Student ID being deleted
            api_key: API key used
            client_ip: Client IP
            duration_ms: Operation duration
            success: Whether deletion succeeded
            reason: Failure reason if applicable
        """
        event = AuditEvent(
            event_id=self._generate_event_id(),
            event_type=AuditEventType.STUDENT_DELETED,
            api_key_fingerprint=self._fingerprint_api_key(api_key) if api_key else None,
            client_ip=client_ip,
            entity_type="student",
            entity_id=student_id,
            operation="soft_delete",
            outcome=AuditOutcome.SUCCESS if success else AuditOutcome.FAILURE,
            outcome_reason=reason,
            duration_ms=duration_ms,
        )
        self.log_event(event)

    def log_auth_failure(
        self,
        api_key_provided: str | None,
        client_ip: str | None = None,
        reason: str = "invalid_api_key",
    ) -> None:
        """Log authentication failure.

        Args:
            api_key_provided: API key that was provided (will be fingerprinted)
            client_ip: Client IP address
            reason: Reason for auth failure (missing, invalid, expired)
        """
        event = AuditEvent(
            event_id=self._generate_event_id(),
            event_type=AuditEventType.AUTH_FAILURE,
            api_key_fingerprint=self._fingerprint_api_key(api_key_provided) if api_key_provided else None,
            client_ip=client_ip,
            entity_type=None,
            entity_id=None,
            operation="authenticate",
            outcome=AuditOutcome.FAILURE,
            outcome_reason=reason,
        )
        self.log_event(event)

    def log_rate_limit_exceeded(
        self,
        client_ip: str | None = None,
        api_key: str | None = None,
        endpoint: str | None = None,
    ) -> None:
        """Log rate limit violation.

        Args:
            client_ip: Client IP that exceeded limit
            api_key: API key used (if any)
            endpoint: Endpoint that was rate limited
        """
        event = AuditEvent(
            event_id=self._generate_event_id(),
            event_type=AuditEventType.RATE_LIMIT_EXCEEDED,
            api_key_fingerprint=self._fingerprint_api_key(api_key) if api_key else None,
            client_ip=client_ip,
            entity_type=None,
            entity_id=None,
            operation="rate_limit_check",
            outcome=AuditOutcome.FAILURE,
            outcome_reason="rate_limit_exceeded",
            metadata={"endpoint": endpoint} if endpoint else None,
        )
        self.log_event(event)

    def log_database_error(
        self,
        operation: str,
        error_message: str,
        entity_type: str | None = None,
        entity_id: int | None = None,
        api_key: str | None = None,
        client_ip: str | None = None,
    ) -> None:
        """Log database error.

        Args:
            operation: Operation that failed
            error_message: Error message from database
            entity_type: Type of entity involved
            entity_id: ID of entity involved
            api_key: API key used
            client_ip: Client IP
        """
        event = AuditEvent(
            event_id=self._generate_event_id(),
            event_type=AuditEventType.DATABASE_ERROR,
            api_key_fingerprint=self._fingerprint_api_key(api_key) if api_key else None,
            client_ip=client_ip,
            entity_type=entity_type,
            entity_id=entity_id,
            operation=operation,
            outcome=AuditOutcome.FAILURE,
            outcome_reason=error_message,
        )
        self.log_event(event)


# Global audit logger instance
audit_logger = AuditLogger()
