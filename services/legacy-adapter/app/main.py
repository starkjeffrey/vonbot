"""FastAPI service for legacy MSSQL database operations.

This service provides a secure REST API for Django to interact with the legacy
MSSQL 2012 database during the phased SIS migration.

Security Features:
- API key authentication
- Rate limiting (60 requests/minute per IP)
- CORS protection
- Request logging and audit trail
- Error handling and validation

Author: Claude Code
Version: 1.0.0
"""

from __future__ import annotations

import logging
from collections import defaultdict
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

from fastapi import Depends, FastAPI, Header, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from .config import settings
from .database import close_connection_pool, get_connection, init_connection_pool
from .models import (
    HealthCheckResponse,
    LegacyAcademicClass,
    LegacyEnrollment,
    LegacyStudentRecord,
    StudentUpdateRequest,
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Simple rate limiting (in-memory, per IP)
# For production with multiple instances, use Redis-based rate limiting
rate_limit_store: dict[str, list[datetime]] = defaultdict(list)


def check_rate_limit(ip: str, limit: int = 60) -> bool:
    """Check if IP has exceeded rate limit (requests per minute).

    Args:
        ip: Client IP address
        limit: Maximum requests per minute (default: 60)

    Returns:
        True if under limit, False if exceeded
    """
    now = datetime.now()
    cutoff = now - timedelta(minutes=1)

    # Clean old requests
    rate_limit_store[ip] = [req_time for req_time in rate_limit_store[ip] if req_time > cutoff]

    # Check limit
    if len(rate_limit_store[ip]) >= limit:
        return False

    # Record this request
    rate_limit_store[ip].append(now)
    return True


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup connection pool."""
    logger.info("🚀 Starting Legacy Adapter Service v1.0.0")
    logger.info(
        "📊 Connecting to MSSQL at %s:%s/%s",
        settings.LEGACY_DB_HOST,
        settings.LEGACY_DB_PORT,
        settings.LEGACY_DB_NAME,
    )
    logger.info("🔒 Security: API Key authentication enabled")
    logger.info("⏱️  Rate limiting: %d requests/minute", settings.RATE_LIMIT_PER_MINUTE)

    init_connection_pool()
    yield

    logger.info("🛑 Shutting down Legacy Adapter Service")
    close_connection_pool()


app = FastAPI(
    title="Legacy SIS Adapter",
    description="Secure bridge service between Django SIS and legacy MSSQL database",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,  # Disable docs in production
    redoc_url="/redoc" if settings.DEBUG else None,
)

# CORS middleware (restrict to your domains)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)

# Trusted host middleware (only in production)
if not settings.DEBUG:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOSTS.split(","))


async def verify_api_key(x_api_key: str = Header(None)):
    """Verify API key for authentication.

    Args:
        x_api_key: API key from X-API-Key header

    Raises:
        HTTPException: 401 if API key is missing or invalid
    """
    if not x_api_key:
        logger.warning("⚠️  Request without API key from %s", "unknown")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="API key required")

    if x_api_key != settings.API_KEY:
        logger.warning("⚠️  Invalid API key attempt: %s...", x_api_key[:10] if x_api_key else "None")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Rate limiting middleware.

    Limits requests to RATE_LIMIT_PER_MINUTE per IP address.
    Health check endpoint is excluded from rate limiting.
    """
    # Skip rate limiting for health check
    if request.url.path == "/health":
        return await call_next(request)

    # Get client IP
    client_ip = request.client.host if request.client else "unknown"

    # Check rate limit
    if not check_rate_limit(client_ip, limit=settings.RATE_LIMIT_PER_MINUTE):
        logger.warning("⚠️  Rate limit exceeded for IP: %s", client_ip)
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"detail": "Rate limit exceeded. Try again later."},
        )

    return await call_next(request)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests for security audit."""
    start_time = datetime.now()

    # Process request
    response = await call_next(request)

    # Calculate duration
    duration = (datetime.now() - start_time).total_seconds()

    # Log request details
    client_ip = request.client.host if request.client else "unknown"
    logger.info(
        "📝 %s %s - %s - %.3fs - IP: %s",
        request.method,
        request.url.path,
        response.status_code,
        duration,
        client_ip,
    )

    return response


@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint (no auth required).

    Returns:
        Health status including database connectivity
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        cursor.close()
        conn.close()

        return HealthCheckResponse(
            status="healthy",
            database="connected",
            timestamp=datetime.now().isoformat(),
        )
    except Exception as e:
        logger.error("❌ Health check failed: %s", str(e))
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "database": "disconnected",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            },
        )


@app.put(
    "/students/{student_id}",
    dependencies=[Depends(verify_api_key)],
)
async def update_student(student_id: str, request: StudentUpdateRequest) -> dict:
    """Update student record in legacy database.

    🔒 Requires API key authentication

    Only updates fields that exist in actual MSSQL schema.
    All fields in StudentUpdateRequest are optional - only provide what you want to update.

    Args:
        student_id: Student ID (maps to legacy 'ID' field)
        request: Update data with legacy column names

    Returns:
        Success message with updated fields

    Raises:
        401: Missing or invalid API key
        404: Student not found
        422: No fields provided
        500: Database error
    """
    logger.info("📝 Updating student: student_id=%s", student_id)

    # Convert Pydantic model to dict, excluding None values
    updates = request.model_dump(exclude_none=True)

    if not updates:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No fields provided for update",
        )

    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Check if student exists
        cursor.execute("SELECT ID FROM Students WHERE ID = %s", (student_id,))
        existing = cursor.fetchone()

        if not existing:
            cursor.close()
            conn.close()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Student with ID {student_id} not found",
            )

        # Build UPDATE query
        set_clause = ", ".join(f"{field} = %s" for field in updates.keys())
        update_sql = f"UPDATE Students SET {set_clause}, ModifiedDate = GETDATE() WHERE ID = %s"

        # Execute update
        cursor.execute(update_sql, (*updates.values(), student_id))

        rows_affected = cursor.rowcount
        conn.commit()
        cursor.close()
        conn.close()

        logger.info("✅ Student updated: student_id=%s, fields=%s", student_id, list(updates.keys()))

        return {
            "success": True,
            "student_id": student_id,
            "updated_fields": list(updates.keys()),
            "message": f"Updated {rows_affected} record(s)",
        }

    except HTTPException:
        raise
    except Exception as e:
        if conn:
            conn.rollback()
            conn.close()
        logger.error("❌ Error updating student: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update student: {e!s}",
        ) from e


# DEPRECATED: CREATE endpoint disabled - legacy schema doesn't match Django assumptions
# Original endpoint tried to insert fields like StudentCode, FirstName, LastName
# which don't exist in actual MSSQL Students table.
# For reference, see models.py StudentCreateRequest (now unused).
#
# @app.post(
#     "/students",
#     response_model=StudentCreateResponse,
#     dependencies=[Depends(verify_api_key)],
# )
# async def create_student(request: StudentCreateRequest) -> StudentCreateResponse:
#     """Create a student record in the legacy database.
#
#     🔒 Requires API key authentication (X-API-Key header)
#     🔒 Rate limited to 60 requests/minute per IP
#
#     This endpoint provides secure write-back to the legacy MSSQL database.
#     Django generates the student_id, and this service writes it to the
#     legacy database for modules that haven't been migrated yet.
#
#     Args:
#         request: Student data from Django
#
#     Returns:
#         StudentCreateResponse with success status and legacy database ID
#
#     Raises:
#         401: Missing or invalid API key
#         409: Student with this student_id already exists
#         429: Rate limit exceeded
#         500: Database error
#     """
#     logger.info("📝 Creating student in legacy DB: student_id=%s", request.student_id)
#
#     # Map Django fields to legacy schema
#     legacy_data = django_student_to_legacy(request)
#
#     conn = None
#     try:
#         conn = get_connection()
#         cursor = conn.cursor()
#
#         # Check for existing student (idempotency)
#         cursor.execute(
#             "SELECT StudentID FROM Students WHERE StudentCode = %s",
#             (request.student_id,),
#         )
#         existing = cursor.fetchone()
#
#         if existing:
#             logger.warning(
#                 "⚠️  Student already exists: student_id=%s, legacy_id=%s",
#                 request.student_id,
#                 existing[0],
#             )
#             cursor.close()
#             conn.close()
#             raise HTTPException(
#                 status_code=status.HTTP_409_CONFLICT,
#                 detail=f"Student with student_id {request.student_id} already exists",
#             )
#
#         # Insert new student record
#         insert_sql = """
#         INSERT INTO Students (
#             StudentCode, FirstName, LastName, MiddleName,
#             EnglishFirstName, EnglishLastName,
#             DateOfBirth, Gender, Email, PhoneNumber,
#             EnrollmentDate, Status, IsMonk, PreferredStudyTime,
#             IsTransferStudent
#         ) VALUES (
#             %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
#         )
#         """
#
#         cursor.execute(
#             insert_sql,
#             (
#                 legacy_data["StudentCode"],
#                 legacy_data["FirstName"],
#                 legacy_data["LastName"],
#                 legacy_data["MiddleName"],
#                 legacy_data["EnglishFirstName"],
#                 legacy_data["EnglishLastName"],
#                 legacy_data["DateOfBirth"],
#                 legacy_data["Gender"],
#                 legacy_data["Email"],
#                 legacy_data["PhoneNumber"],
#                 legacy_data["EnrollmentDate"],
#                 legacy_data["Status"],
#                 legacy_data["IsMonk"],
#                 legacy_data["PreferredStudyTime"],
#                 legacy_data["IsTransferStudent"],
#             ),
#         )
#
#         # Get the generated legacy StudentID (IDENTITY column)
#         cursor.execute("SELECT @@IDENTITY AS StudentID")
#         result = cursor.fetchone()
#         legacy_student_id = result[0] if result else None
#
#         conn.commit()
#         cursor.close()
#         conn.close()
#
#         logger.info(
#             "✅ Student created: student_id=%s, legacy_id=%s",
#             request.student_id,
#             legacy_student_id,
#         )
#
#         return StudentCreateResponse(
#             success=True,
#             student_id=request.student_id,
#             legacy_student_id=legacy_student_id,
#             message="Student record created in legacy database",
#         )
#
#     except pymssql.IntegrityError as e:
#         if conn:
#             conn.rollback()
#             conn.close()
#         logger.error("❌ Integrity error: %s", str(e))
#         raise HTTPException(
#             status_code=status.HTTP_409_CONFLICT,
#             detail=f"Database constraint violation: {e!s}",
#         ) from e
#     except HTTPException:
#         # Re-raise HTTP exceptions as-is
#         raise
#     except Exception as e:
#         if conn:
#             conn.rollback()
#             conn.close()
#         logger.error("❌ Error creating student: %s", str(e))
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Failed to create student in legacy database: {e!s}",
#         ) from e


@app.get(
    "/students/{student_id}",
    response_model=LegacyStudentRecord | None,
    dependencies=[Depends(verify_api_key)],
)
async def get_student(student_id: str) -> LegacyStudentRecord | None:
    """Retrieve student record from legacy database.

    🔒 Requires API key authentication

    Args:
        student_id: Student ID (maps to legacy 'ID' field)

    Returns:
        Student record or None if not found

    Raises:
        401: Missing or invalid API key
        500: Database error
    """
    logger.info("🔍 Fetching student: student_id=%s", student_id)

    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor(as_dict=True)

        # Query actual legacy schema fields
        cursor.execute(
            """
            SELECT
                ID, Name, KName, BirthDate, BirthPlace, Gender,
                Email, MobilePhone, HomePhone, HomeAddress,
                Status, Admitted, Deleted,
                AdmissionDate, AdmissionDateForUnder, AdmissionDateForMaster,
                SelectedProgram, SelectedMajor, SelectedFaculty,
                Firstenroll, Lastenroll,
                BAStartDate, BAEndDate, MAStartDate, MAEndDate,
                Transfer, CreatedDate, ModifiedDate
            FROM Students
            WHERE ID = %s
            """,
            (student_id,),
        )

        result = cursor.fetchone()
        cursor.close()
        conn.close()

        if not result:
            logger.warning("⚠️  Student not found: student_id=%s", student_id)
            return None

        logger.info("✅ Student found: student_id=%s", student_id)
        return LegacyStudentRecord(**result)

    except Exception as e:
        if conn:
            conn.close()
        logger.error("❌ Error fetching student: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch student from legacy database: {e!s}",
        ) from e


@app.delete("/students/{student_id}", dependencies=[Depends(verify_api_key)])
async def delete_student(student_id: str) -> dict:
    """Soft delete student in legacy database.

    🔒 Requires API key authentication

    Note: This sets status to 'Inactive' rather than hard delete.

    Args:
        student_id: Student ID (maps to legacy 'ID' field)

    Returns:
        Success message

    Raises:
        401: Missing or invalid API key
        404: Student not found
        500: Database error
    """
    logger.info("🗑️  Soft deleting student: student_id=%s", student_id)

    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "UPDATE Students SET Status = 'Inactive' WHERE ID = %s",
            (student_id,),
        )

        rows_affected = cursor.rowcount
        conn.commit()
        cursor.close()
        conn.close()

        if rows_affected == 0:
            logger.warning("⚠️  Student not found for deletion: student_id=%s", student_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Student with student_id {student_id} not found",
            )

        logger.info("✅ Student soft deleted: student_id=%s", student_id)
        return {"success": True, "message": "Student marked as inactive"}

    except HTTPException:
        raise
    except Exception as e:
        if conn:
            conn.rollback()
            conn.close()
        logger.error("❌ Error soft deleting student: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete student: {e!s}",
        ) from e


@app.get(
    "/enrollments",
    response_model=list[LegacyEnrollment],
    dependencies=[Depends(verify_api_key)],
)
async def get_enrollments(
    term: str | None = None,
    course: str | None = None,
    student: str | None = None,
) -> list[LegacyEnrollment]:
    """Retrieve enrollment records from legacy AcademicCourseTakers table.

    🔒 Requires API key authentication

    Query enrollments with optional filters. At least one filter should be provided
    for performance reasons (querying all enrollments is slow).

    Term format: ClassID prefix before first !$ delimiter (e.g., "251027E-T4BE")

    Args:
        term: Filter by term (ClassID prefix, e.g., "251027E-T4BE")
        course: Filter by course code (e.g., "EHSS-02")
        student: Filter by student ID

    Returns:
        List of enrollment records matching filters

    Raises:
        401: Missing or invalid API key
        422: No filters provided
        500: Database error

    Examples:
        GET /enrollments?term=251027E-T4BE
        GET /enrollments?term=251027E-T4BE&course=EHSS-02
        GET /enrollments?student=18405
    """
    logger.info("🔍 Fetching enrollments: term=%s, course=%s, student=%s", term, course, student)

    # Require at least one filter for performance
    if not any([term, course, student]):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="At least one filter (term, course, or student) is required",
        )

    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor(as_dict=True)

        # Build WHERE clause dynamically based on provided filters
        where_conditions = []
        params = []

        if term:
            # Term is the ClassID prefix before first !$
            where_conditions.append("ClassID LIKE %s")
            params.append(f"{term}!$%")

        if course:
            # Course code filter (may need to parse from ClassID or use NormalizedCourse)
            where_conditions.append("NormalizedCourse LIKE %s")
            params.append(f"%{course}%")

        if student:
            where_conditions.append("ID = %s")
            params.append(student)

        where_clause = " AND ".join(where_conditions)

        # Query AcademicCourseTakers table
        query = f"""
            SELECT
                IPK, ID, ClassID, RepeatNum, LScore, UScore,
                Credit, GradePoint, TotalPoint, Grade, PreviousGrade,
                Passed, Remarks, RegisterMode, Attendance,
                AddTime, LastUpdate,
                NormalizedCourse, NormalizedPart, NormalizedSection
            FROM AcademicCourseTakers
            WHERE {where_clause}
            ORDER BY ClassID, ID
        """

        cursor.execute(query, tuple(params))
        results = cursor.fetchall()
        cursor.close()
        conn.close()

        logger.info("✅ Found %d enrollment records", len(results))

        # Convert to LegacyEnrollment models
        return [LegacyEnrollment(**row) for row in results]

    except HTTPException:
        raise
    except Exception as e:
        if conn:
            conn.close()
        logger.error("❌ Error fetching enrollments: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch enrollments from legacy database: {e!s}",
        ) from e


@app.get(
    "/classes",
    response_model=list[LegacyAcademicClass],
    dependencies=[Depends(verify_api_key)],
)
async def get_classes(
    term: str | None = None,
    course: str | None = None,
) -> list[LegacyAcademicClass]:
    """Retrieve class records from legacy AcademicClasses table.

    🔒 Requires API key authentication

    Query class sections with optional filters. Returns class metadata including
    ClassID, course codes, normalized section/part information.

    Term format: TermID field value (e.g., "251027E-T4BE")

    Args:
        term: Filter by term (TermID field, e.g., "251027E-T4BE")
        course: Filter by course code (e.g., "EHSS-02")

    Returns:
        List of class records matching filters

    Raises:
        401: Missing or invalid API key
        422: No filters provided
        500: Database error

    Examples:
        GET /classes?term=251027E-T4BE
        GET /classes?term=251027E-T4BE&course=EHSS-02
    """
    logger.info("🔍 Fetching classes: term=%s, course=%s", term, course)

    # Require at least one filter for performance
    if not any([term, course]):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="At least one filter (term or course) is required",
        )

    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor(as_dict=True)

        # Build WHERE clause dynamically
        where_conditions = []
        params = []

        if term:
            where_conditions.append("TermID = %s")
            params.append(term)

        if course:
            where_conditions.append("NormalizedCourse LIKE %s")
            params.append(f"%{course}%")

        where_clause = " AND ".join(where_conditions)

        # Query AcademicClasses table
        query = f"""
            SELECT
                IPK, TermID, Program, Major, GroupID, CourseCode, ClassID,
                CourseTitle, StNumber, CourseType, SchoolTime, Subject,
                NormalizedCourse, NormalizedPart, NormalizedSection, NormalizedTOD,
                CreatedDate, ModifiedDate
            FROM AcademicClasses
            WHERE {where_clause}
            ORDER BY ClassID
        """

        cursor.execute(query, tuple(params))
        results = cursor.fetchall()
        cursor.close()
        conn.close()

        logger.info("✅ Found %d class records", len(results))

        # Convert to LegacyAcademicClass models
        return [LegacyAcademicClass(**row) for row in results]

    except HTTPException:
        raise
    except Exception as e:
        if conn:
            conn.close()
        logger.error("❌ Error fetching classes: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch classes from legacy database: {e!s}",
        ) from e
