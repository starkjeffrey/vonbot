# Testing Guide for Legacy Adapter Service

<!-- Last Updated: 2025-01-30 -->

This guide covers the comprehensive test suite for the legacy adapter service, including unit tests, integration tests, security tests, and audit controls.

## 🎯 Test Philosophy

The legacy adapter follows a **test pyramid** approach:

```
        /\
       /  \      E2E Tests (Future)
      /____\
     /      \    Integration Tests (API endpoints)
    /________\
   /          \  Unit Tests (mappers, models, logic)
  /____________\
```

- **Unit Tests**: Fast, isolated, no external dependencies (mocked database)
- **Integration Tests**: Test complete request/response cycles with mocked database
- **Security Tests**: Verify authentication, authorization, rate limiting
- **Contract Tests**: Ensure compatibility with legacy MSSQL schema

## 🚀 Quick Start

### Install Test Dependencies

```bash
# Install production dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt
```

### Run All Tests

```bash
# Run all tests with verbose output
pytest -v

# Run with coverage report
pytest --cov=app --cov-report=term-missing --cov-report=html

# Run specific test categories
pytest -m unit          # Only unit tests (fast)
pytest -m integration   # Only integration tests
pytest -m security      # Only security tests
```

## 📁 Test Structure

```
tests/
├── conftest.py                 # Shared fixtures and configuration
├── test_mappers.py            # Unit tests for schema mappers
├── test_api_endpoints.py      # Integration tests for API
├── test_audit.py              # Unit tests for audit system
└── test_models.py             # Unit tests for Pydantic models (future)
```

## 🧪 Test Categories

### Unit Tests (`@pytest.mark.unit`)

**Purpose**: Test individual components in isolation

**Characteristics**:
- Fast execution (milliseconds)
- No external dependencies
- Mocked database connections
- High code coverage

**Examples**:
```python
# tests/test_mappers.py
@pytest.mark.unit
def test_django_to_legacy_mapping():
    """Test Django student data maps correctly to legacy schema."""
    request = StudentCreateRequest(...)
    result = django_student_to_legacy(request)
    assert result["StudentCode"] == 12345
```

**Run unit tests only**:
```bash
pytest -m unit -v
```

### Integration Tests (`@pytest.mark.integration`)

**Purpose**: Test API endpoints end-to-end with mocked database

**Characteristics**:
- Test complete request/response cycle
- Mock database connections
- Verify authentication, validation, error handling
- Test middleware (rate limiting, CORS)

**Examples**:
```python
# tests/test_api_endpoints.py
@pytest.mark.integration
def test_create_student_success(client, auth_headers, mock_db_connection):
    """Test successful student creation via API."""
    response = client.post("/students", json=data, headers=auth_headers)
    assert response.status_code == 200
```

**Run integration tests only**:
```bash
pytest -m integration -v
```

### Security Tests (`@pytest.mark.security`)

**Purpose**: Verify security controls work correctly

**Characteristics**:
- Test authentication (API key validation)
- Test authorization (endpoint access control)
- Test rate limiting enforcement
- Test input validation (injection prevention)

**Examples**:
```python
# tests/test_api_endpoints.py
@pytest.mark.security
def test_missing_api_key(client):
    """Test request without API key is rejected."""
    response = client.post("/students", json=data)
    assert response.status_code == 401
```

**Run security tests only**:
```bash
pytest -m security -v
```

### Contract Tests (`@pytest.mark.contract`)

**Purpose**: Ensure compatibility with legacy MSSQL schema

**Characteristics**:
- Verify field mappings match actual legacy schema
- Test backward compatibility after changes
- Validate data type conversions

**Run contract tests**:
```bash
pytest -m contract -v
```

## 🔧 Test Fixtures

### Shared Fixtures (conftest.py)

**`client`**: FastAPI test client with mocked database
```python
def test_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
```

**`auth_headers`**: Valid API key headers for authenticated requests
```python
def test_authenticated_endpoint(client, auth_headers):
    response = client.post("/students", json=data, headers=auth_headers)
```

**`mock_db_connection`**: Mocked pymssql connection
```python
def test_database_operation(mock_db_connection):
    mock_cursor = mock_db_connection.cursor.return_value
    mock_cursor.fetchone.return_value = [1]
```

**`sample_student_request`**: Sample student creation payload
```python
def test_student_creation(client, auth_headers, sample_student_request):
    response = client.post("/students", json=sample_student_request, headers=auth_headers)
```

**`sample_legacy_record`**: Sample legacy database record
```python
def test_legacy_mapping(sample_legacy_record):
    result = legacy_student_to_django(sample_legacy_record)
```

## 📊 Coverage Goals

| Component | Target Coverage |
|-----------|----------------|
| Mappers | 100% |
| Models | 100% |
| API Endpoints | 95%+ |
| Database | 90%+ |
| Middleware | 95%+ |
| Overall | 90%+ |

**Generate coverage report**:
```bash
# Terminal output
pytest --cov=app --cov-report=term-missing

# HTML report (open htmlcov/index.html)
pytest --cov=app --cov-report=html
```

## 🐛 Debugging Tests

### Run Single Test

```bash
# Run specific test function
pytest tests/test_mappers.py::TestDjangoToLegacyMapping::test_monk_gender_mapping -v

# Run specific test class
pytest tests/test_mappers.py::TestDjangoToLegacyMapping -v

# Run specific test file
pytest tests/test_mappers.py -v
```

### Show Print Statements

```bash
# Disable output capture to see print() and logging
pytest -s
```

### Show Full Traceback

```bash
# Long traceback format
pytest --tb=long

# Short traceback (default)
pytest --tb=short

# No traceback
pytest --tb=no
```

### Stop on First Failure

```bash
pytest -x  # Stop after first failure
pytest --maxfail=3  # Stop after 3 failures
```

### Run Last Failed Tests

```bash
pytest --lf  # Run only tests that failed last time
pytest --ff  # Run failed tests first, then all others
```

## 🔍 Test-Driven Development Workflow

### 1. Write Failing Test

```python
# tests/test_new_feature.py
@pytest.mark.unit
def test_new_mapper_function():
    """Test new mapper handles edge case."""
    result = new_mapper_function(edge_case_data)
    assert result == expected_output  # This will fail initially
```

### 2. Run Test (Should Fail)

```bash
pytest tests/test_new_feature.py -v
# Expected: FAILED - Function doesn't exist yet
```

### 3. Implement Minimum Code

```python
# app/mappers.py
def new_mapper_function(data):
    return expected_output  # Simplest implementation
```

### 4. Run Test Again (Should Pass)

```bash
pytest tests/test_new_feature.py -v
# Expected: PASSED
```

### 5. Refactor and Verify

```python
# app/mappers.py
def new_mapper_function(data):
    # Proper implementation with error handling
    ...
```

```bash
pytest tests/test_new_feature.py -v
# Expected: PASSED
```

## 🔒 Testing Security Features

### API Key Authentication

```python
# Test missing API key
def test_no_api_key(client):
    response = client.post("/students", json=data)
    assert response.status_code == 401

# Test invalid API key
def test_invalid_api_key(client):
    headers = {"X-API-Key": "wrong-key"}
    response = client.post("/students", json=data, headers=headers)
    assert response.status_code == 401

# Test valid API key
def test_valid_api_key(client, auth_headers):
    response = client.post("/students", json=data, headers=auth_headers)
    assert response.status_code == 200
```

### Rate Limiting

```python
# Test rate limit enforcement
def test_rate_limit(client, auth_headers):
    # Make 60 requests (limit)
    for _ in range(60):
        response = client.post("/students", json=data, headers=auth_headers)

    # 61st request should fail
    response = client.post("/students", json=data, headers=auth_headers)
    assert response.status_code == 429
```

### Input Validation

```python
# Test SQL injection prevention
def test_sql_injection_prevention(client, auth_headers):
    malicious_data = {
        "first_name": "'; DROP TABLE Students; --",
        ...
    }
    # Should be safely parameterized, not cause error
    response = client.post("/students", json=malicious_data, headers=auth_headers)
```

## 📈 Continuous Integration

### Pre-commit Checks

```bash
# Run before committing
pytest -v
pytest --cov=app --cov-report=term-missing
ruff check .
mypy app/
```

### CI Pipeline (GitHub Actions Example)

```yaml
# .github/workflows/test.yml
name: Test Legacy Adapter

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.14'
      - run: pip install -r requirements.txt -r requirements-dev.txt
      - run: pytest --cov=app --cov-report=xml
      - run: ruff check .
      - run: mypy app/
```

## 🎓 Best Practices

### 1. Test Naming

```python
# ✅ GOOD: Descriptive test names
def test_create_student_success_returns_legacy_id():
    ...

def test_create_student_with_duplicate_id_returns_409():
    ...

# ❌ BAD: Vague test names
def test_student_1():
    ...

def test_edge_case():
    ...
```

### 2. Arrange-Act-Assert Pattern

```python
def test_student_mapping():
    # Arrange - Set up test data
    request = StudentCreateRequest(...)

    # Act - Execute function under test
    result = django_student_to_legacy(request)

    # Assert - Verify results
    assert result["StudentCode"] == 12345
    assert result["Gender"] == "M"
```

### 3. One Assertion Per Concept

```python
# ✅ GOOD: Test one concept, multiple related assertions
def test_monk_gender_mapping():
    result = django_student_to_legacy(monk_request)
    assert result["Gender"] == "Monk"
    assert result["IsMonk"] is True

# ❌ BAD: Testing multiple unrelated concepts
def test_everything():
    assert gender_mapping() == "M"
    assert status_mapping() == "Active"
    assert email_validation() == True
```

### 4. Use Fixtures for Reusable Data

```python
# ✅ GOOD: Use fixtures
def test_student_creation(sample_student_request):
    result = process_student(sample_student_request)
    ...

# ❌ BAD: Duplicate data in every test
def test_student_creation():
    data = {"student_id": 12345, "first_name": "Sopheak", ...}
    result = process_student(data)
```

## 🚨 Common Issues

### Issue: Tests Pass Locally But Fail in CI

**Cause**: Timing issues, environment differences

**Solution**:
```python
# Use freezegun for time-dependent tests
from freezegun import freeze_time

@freeze_time("2024-01-30 12:00:00")
def test_time_dependent_feature():
    ...
```

### Issue: Flaky Tests (Intermittent Failures)

**Cause**: Race conditions, non-deterministic behavior

**Solution**:
```python
# Use deterministic test data
@pytest.fixture
def student_request():
    return StudentCreateRequest(
        student_id=12345,  # Fixed ID, not random
        ...
    )
```

### Issue: Slow Test Suite

**Solution**:
```bash
# Run tests in parallel
pip install pytest-xdist
pytest -n auto  # Use all CPU cores
```

## 📚 Additional Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing Guide](https://fastapi.tiangolo.com/tutorial/testing/)
- [Testing Best Practices](https://docs.python-guide.org/writing/tests/)
- [Pydantic Testing](https://docs.pydantic.dev/latest/concepts/testing/)
