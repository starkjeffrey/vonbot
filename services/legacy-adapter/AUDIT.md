# Audit Controls and Compliance Guide

<!-- Last Updated: 2025-01-30 -->

This guide covers the audit logging system for the legacy adapter service, including audit event types, structured logging, compliance features, and analysis tools.

## 🎯 Purpose

The audit system provides:
- **Compliance**: Immutable audit trail for all database operations
- **Security Monitoring**: Detection of unauthorized access attempts
- **Troubleshooting**: Detailed operation logs for debugging
- **Analytics**: Usage patterns and performance metrics

## 🏗️ Architecture

```
┌─────────────────────────────────────┐
│ API Endpoint                        │
│ (create_student, get_student, etc.) │
└──────────────┬──────────────────────┘
               │
               ├─> Operation Execution
               │
               └─> audit_logger.log_*()
                   │
                   ├─> Structured JSON Event
                   │   (event_id, timestamp, actor, outcome)
                   │
                   └─> Logging System
                       │
                       ├─> stdout (Docker logs)
                       ├─> File (audit.log)
                       └─> External System (future: Splunk, ELK)
```

## 📊 Audit Event Types

### Student Operations

| Event Type | Description | Triggered When |
|------------|-------------|----------------|
| `student.created` | Student record created | POST /students succeeds |
| `student.read` | Student record accessed | GET /students/{id} |
| `student.updated` | Student record modified | PUT /students/{id} (future) |
| `student.deleted` | Student soft deleted | DELETE /students/{id} |

### Authentication Events

| Event Type | Description | Triggered When |
|------------|-------------|----------------|
| `auth.success` | Valid API key used | Any authenticated request |
| `auth.failure` | Invalid API key | Wrong API key provided |
| `auth.missing` | No API key | Request without X-API-Key header |

### Security Events

| Event Type | Description | Triggered When |
|------------|-------------|----------------|
| `rate_limit.exceeded` | Rate limit violation | > 60 requests/minute from IP |

### System Events

| Event Type | Description | Triggered When |
|------------|-------------|----------------|
| `system.health_check` | Health check performed | GET /health |
| `system.started` | Service started | Application startup |
| `system.stopped` | Service stopped | Application shutdown |

### Error Events

| Event Type | Description | Triggered When |
|------------|-------------|----------------|
| `error.database` | Database error | MSSQL connection/query failure |
| `error.validation` | Validation error | Invalid request data |
| `error.internal` | Internal error | Unexpected exception |

## 📝 Audit Event Structure

### JSON Schema

```json
{
  "event_id": "20240130-120000-000001",
  "event_type": "student.created",
  "timestamp": "2024-01-30T12:00:00.000Z",
  "actor": {
    "api_key_fingerprint": "abc123def456",
    "client_ip": "192.168.1.100",
    "user_agent": "Django/4.2"
  },
  "operation": {
    "entity_type": "student",
    "entity_id": 12345,
    "action": "create"
  },
  "outcome": {
    "status": "success",
    "reason": null,
    "duration_ms": 123.45
  },
  "metadata": {
    "legacy_student_id": 999
  }
}
```

### Field Descriptions

| Field | Description | Example |
|-------|-------------|---------|
| `event_id` | Unique event identifier | `20240130-120000-000001` |
| `event_type` | Type of event (enum) | `student.created` |
| `timestamp` | UTC timestamp (ISO 8601) | `2024-01-30T12:00:00.000Z` |
| `actor.api_key_fingerprint` | SHA256 hash of API key (first 16 chars) | `abc123def456` |
| `actor.client_ip` | Client IP address | `192.168.1.100` |
| `actor.user_agent` | HTTP User-Agent header | `Django/4.2` |
| `operation.entity_type` | Entity type affected | `student` |
| `operation.entity_id` | ID of affected entity | `12345` |
| `operation.action` | Action performed | `create`, `read`, `update`, `delete` |
| `outcome.status` | Operation result | `success`, `failure`, `partial` |
| `outcome.reason` | Failure reason (if applicable) | `duplicate_student_id` |
| `outcome.duration_ms` | Operation duration | `123.45` |
| `metadata` | Additional event-specific data | `{"legacy_student_id": 999}` |

## 🔧 Integration Examples

### Basic Usage

```python
from app.audit import audit_logger

# Log successful student creation
audit_logger.log_student_created(
    student_id=12345,
    legacy_student_id=999,
    api_key="your-api-key",
    client_ip="192.168.1.100",
    duration_ms=150.0,
    success=True
)

# Log failed student creation
audit_logger.log_student_created(
    student_id=12345,
    legacy_student_id=None,
    api_key="your-api-key",
    client_ip="192.168.1.100",
    duration_ms=50.0,
    success=False,
    reason="duplicate_student_id"
)
```

### API Endpoint Integration

```python
from datetime import datetime
from app.audit import audit_logger

@app.post("/students")
async def create_student(
    request: Request,
    data: StudentCreateRequest,
    x_api_key: str = Header(None)
):
    start_time = datetime.now()
    client_ip = request.client.host

    try:
        # Create student in database
        legacy_id = create_student_in_db(data)

        # Calculate duration
        duration_ms = (datetime.now() - start_time).total_seconds() * 1000

        # Log successful creation
        audit_logger.log_student_created(
            student_id=data.student_id,
            legacy_student_id=legacy_id,
            api_key=x_api_key,
            client_ip=client_ip,
            duration_ms=duration_ms,
            success=True
        )

        return {"success": True, "legacy_student_id": legacy_id}

    except Exception as e:
        duration_ms = (datetime.now() - start_time).total_seconds() * 1000

        # Log failed creation
        audit_logger.log_student_created(
            student_id=data.student_id,
            legacy_student_id=None,
            api_key=x_api_key,
            client_ip=client_ip,
            duration_ms=duration_ms,
            success=False,
            reason=str(e)
        )

        raise
```

### Authentication Failure Logging

```python
async def verify_api_key(x_api_key: str = Header(None), request: Request = None):
    """Verify API key and log auth failures."""
    client_ip = request.client.host if request else None

    if not x_api_key:
        audit_logger.log_auth_failure(
            api_key_provided=None,
            client_ip=client_ip,
            reason="missing_api_key"
        )
        raise HTTPException(status_code=401, detail="API key required")

    if x_api_key != settings.API_KEY:
        audit_logger.log_auth_failure(
            api_key_provided=x_api_key,
            client_ip=client_ip,
            reason="invalid_api_key"
        )
        raise HTTPException(status_code=401, detail="Invalid API key")
```

## 📈 Monitoring and Analysis

### View Audit Logs

```bash
# Docker logs (stdout)
docker compose -f docker-compose.vps.yml logs -f | grep audit

# Filter by event type
docker compose logs -f | grep '"event_type": "student.created"'

# Filter by outcome
docker compose logs -f | grep '"status": "failure"'

# Filter by IP address
docker compose logs -f | grep '"client_ip": "192.168.1.100"'
```

### Parse JSON Logs

```bash
# Extract all failed operations
docker compose logs | grep audit | jq 'select(.outcome.status == "failure")'

# Count events by type
docker compose logs | grep audit | jq -r '.event_type' | sort | uniq -c

# Get average operation duration
docker compose logs | grep audit | jq -r '.outcome.duration_ms' | awk '{sum+=$1; count++} END {print sum/count}'

# Find all auth failures in last hour
docker compose logs --since=1h | grep auth.failure
```

### Common Queries

**Failed student creations**:
```bash
docker compose logs | grep audit | jq 'select(.event_type == "student.created" and .outcome.status == "failure")'
```

**Rate limit violations by IP**:
```bash
docker compose logs | grep audit | jq 'select(.event_type == "rate_limit.exceeded") | .actor.client_ip' | sort | uniq -c
```

**Operations by API key**:
```bash
docker compose logs | grep audit | jq -r '.actor.api_key_fingerprint' | sort | uniq -c
```

**Slowest operations**:
```bash
docker compose logs | grep audit | jq -r '"\(.outcome.duration_ms)\t\(.event_type)\t\(.operation.entity_id)"' | sort -rn | head -20
```

## 🔒 Security Features

### API Key Fingerprinting

API keys are NEVER logged in plaintext. Instead, we log a SHA256 fingerprint:

```python
# Original API key: "my-super-secret-api-key-12345"
# Logged fingerprint: "abc123def456" (first 16 chars of SHA256)
```

**Benefits**:
- Audit logs can be shared without exposing API keys
- Unique fingerprint per API key for tracking
- Irreversible (cannot recover API key from fingerprint)

### Immutable Audit Trail

Audit logs are append-only:
- Events are written to stdout/file immediately
- No delete or update operations
- Timestamped with UTC timezone
- Unique event IDs prevent duplication

### Compliance Features

- **GDPR**: Personal data can be redacted while preserving audit integrity
- **SOC2**: Complete audit trail of all database operations
- **HIPAA**: Access logs for protected health information
- **ISO 27001**: Security event monitoring and logging

## 📊 Metrics and Dashboards

### Key Metrics to Monitor

| Metric | Description | Alert Threshold |
|--------|-------------|-----------------|
| Failed operations | `outcome.status == "failure"` | > 5% failure rate |
| Auth failures | `event_type == "auth.failure"` | > 10/minute from single IP |
| Rate limit hits | `event_type == "rate_limit.exceeded"` | > 100/hour |
| Slow operations | `outcome.duration_ms > 1000` | > 5% of operations |
| Database errors | `event_type == "error.database"` | Any occurrence |

### Sample Dashboard Queries (ELK Stack)

```
# Failed operations trend
event_type:*.* AND outcome.status:failure

# Top error reasons
event_type:error.* | stats count by outcome.reason

# Operations by hour
event_type:student.* | timechart span=1h count by event_type

# Geographic distribution (if client_ip is geolocated)
actor.client_ip:* | iplocation actor.client_ip | geostats count
```

## 🧪 Testing Audit Logging

### Unit Tests

```python
# tests/test_audit.py
@patch("app.audit.logging.getLogger")
def test_log_student_created_success(mock_get_logger):
    """Test successful student creation logging."""
    mock_logger = MagicMock()
    mock_get_logger.return_value = mock_logger

    logger = AuditLogger()
    logger.logger = mock_logger

    logger.log_student_created(
        student_id=12345,
        legacy_student_id=999,
        api_key="test-key",
        client_ip="192.168.1.100",
        success=True
    )

    # Verify logger.info was called
    assert mock_logger.info.called

    # Verify JSON structure
    call_args = mock_logger.info.call_args[0][0]
    data = json.loads(call_args)
    assert data["event_type"] == "student.created"
    assert data["outcome"]["status"] == "success"
```

### Integration Tests

```python
# Test that API endpoints trigger audit logs
def test_create_student_logs_audit_event(client, auth_headers, mock_logger):
    response = client.post("/students", json=data, headers=auth_headers)

    # Verify audit log was written
    assert mock_logger.info.called
    log_data = json.loads(mock_logger.info.call_args[0][0])
    assert log_data["event_type"] == "student.created"
```

## 🚀 Production Deployment

### Log Rotation

```yaml
# docker-compose.vps.yml
services:
  legacy-adapter:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "5"
```

### External Log Aggregation

```python
# Send audit logs to external system (future enhancement)
import logging.handlers

# Syslog handler
syslog_handler = logging.handlers.SysLogHandler(
    address=('syslog-server.example.com', 514)
)
audit_logger.addHandler(syslog_handler)

# HTTP handler (for ELK, Splunk)
from logging.handlers import HTTPHandler
http_handler = HTTPHandler(
    'elk-server.example.com:9200',
    '/audit-logs/_doc',
    method='POST'
)
audit_logger.addHandler(http_handler)
```

### Retention Policies

```bash
# Keep audit logs for 90 days (compliance requirement)
find /var/log/audit -name "*.log" -mtime +90 -delete

# Archive to S3 before deletion
aws s3 sync /var/log/audit s3://audit-archive/legacy-adapter/
```

## 📚 Best Practices

### 1. Always Log Both Success and Failure

```python
# ✅ GOOD: Log both outcomes
try:
    result = create_student(data)
    audit_logger.log_student_created(..., success=True)
except Exception as e:
    audit_logger.log_student_created(..., success=False, reason=str(e))
    raise

# ❌ BAD: Only log failures
try:
    result = create_student(data)
except Exception as e:
    audit_logger.log_student_created(..., success=False)
```

### 2. Include Operation Duration

```python
# ✅ GOOD: Track performance
start_time = datetime.now()
result = operation()
duration_ms = (datetime.now() - start_time).total_seconds() * 1000
audit_logger.log_event(..., duration_ms=duration_ms)
```

### 3. Provide Context in Metadata

```python
# ✅ GOOD: Rich context
audit_logger.log_student_created(
    ...,
    metadata={
        "legacy_student_id": 999,
        "source": "django_sync",
        "batch_id": "20240130-001"
    }
)
```

### 4. Never Log Sensitive Data

```python
# ❌ BAD: Logging sensitive data
audit_logger.log_event(..., metadata={"password": user_password})

# ✅ GOOD: Log only non-sensitive data
audit_logger.log_event(..., metadata={"password_changed": True})
```

## 🔍 Troubleshooting

### No Audit Logs Appearing

```bash
# Check audit logger configuration
python -c "import logging; logging.getLogger('audit').setLevel(logging.INFO)"

# Verify log level in config
grep LOG_LEVEL .env
```

### Audit Logs Not Parsed Correctly

```bash
# Validate JSON structure
docker compose logs | grep audit | jq .

# Check for malformed JSON
docker compose logs | grep audit | grep -v "^{" | grep -v "^}"
```

### Performance Impact

```python
# Audit logging should be async in production
import logging.handlers
from queue import Queue

# Use QueueHandler for async logging
queue = Queue()
queue_handler = logging.handlers.QueueHandler(queue)
audit_logger.addHandler(queue_handler)
```

## 📚 Additional Resources

- [Audit Logging Best Practices](https://owasp.org/www-community/Logging_Cheat_Sheet)
- [Python Logging Documentation](https://docs.python.org/3/library/logging.html)
- [Structured Logging with JSON](https://www.structlog.org/)
