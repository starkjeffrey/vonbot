"""Schema mapping between Django and legacy database.

IMPORTANT NOTES:
1. Legacy has quirky gender mapping: M, F, Monk (not a separate field!)
   Django separates this into gender (M/F/N/X) + is_monk (boolean)

2. Legacy database is likely MISSING many fields that Django has.
   When writing to legacy, we only send fields that legacy schema supports.
   When reading from legacy, we provide sensible defaults for missing data.

3. Field naming conventions differ:
   - Django: snake_case (first_name, enrollment_date)
   - Legacy: PascalCase (FirstName, EnrollmentDate)
"""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .models import StudentCreateRequest


def django_student_to_legacy(django_student: StudentCreateRequest) -> dict[str, Any]:
    """Map Django StudentProfile + Person fields to legacy Students table schema.

    This function handles the impedance mismatch between Django's clean
    architecture and the legacy MSSQL schema.

    Args:
        django_student: Student data from Django

    Returns:
        Dictionary with legacy table column names and values

    Examples:
        >>> request = StudentCreateRequest(
        ...     student_id=12345,
        ...     first_name="Sopheak",
        ...     last_name="Chan",
        ...     date_of_birth=date(2000, 1, 15),
        ...     gender="M"
        ... )
        >>> legacy = django_student_to_legacy(request)
        >>> legacy['StudentCode']
        12345
        >>> legacy['Gender']
        'M'
    """
    # Map Django gender choices to legacy values
    # Django uses: M (Male), F (Female), N (Non-binary), X (Prefer not to say)
    # Django also has separate is_monk field (boolean)
    # Legacy uses: M (Male), F (Female), Monk (gender value, not separate field!)
    #
    # Mapping strategy:
    # - If is_monk=True → use "Monk" as gender in legacy (regardless of actual gender)
    # - Otherwise use standard gender mapping
    if django_student.is_monk:
        legacy_gender = "Monk"
    else:
        gender_map = {
            "M": "M",  # Male
            "F": "F",  # Female
            "N": "M",  # Non-binary → default to M (legacy has no equivalent)
            "X": "M",  # Prefer not to say → default to M (legacy has no equivalent)
        }
        legacy_gender = gender_map.get(django_student.gender, "M")

    # Map Django status to legacy status
    # Django uses: ACTIVE, INACTIVE, GRADUATED, etc.
    # Legacy uses: Active, Inactive, Graduated, etc. (Title Case)
    status_map = {
        "ACTIVE": "Active",
        "INACTIVE": "Inactive",
        "GRADUATED": "Graduated",
        "DROPPED": "Dropped",
        "SUSPENDED": "Suspended",
        "TRANSFERRED": "Transferred",
        "FROZEN": "Frozen",
        "UNKNOWN": "Unknown",
    }

    # Map study time preferences
    # Django uses: morning, afternoon, evening (lowercase)
    # Legacy uses: Morning, Afternoon, Evening (Title Case)
    study_time_map = {
        "morning": "Morning",
        "afternoon": "Afternoon",
        "evening": "Evening",
    }

    return {
        # Primary identifier - Django-generated student_id is source of truth!
        "StudentCode": django_student.student_id,
        # Name fields
        "FirstName": django_student.first_name,
        "LastName": django_student.last_name,
        "MiddleName": django_student.middle_name,
        "EnglishFirstName": django_student.english_first_name,
        "EnglishLastName": django_student.english_last_name,
        # Demographic fields
        "DateOfBirth": django_student.date_of_birth,
        "Gender": legacy_gender,  # Uses monk-aware mapping from above
        # Contact information
        "Email": django_student.email,
        "PhoneNumber": django_student.phone_number,
        # Enrollment information
        "EnrollmentDate": django_student.enrollment_date or date.today(),
        "Status": status_map.get(django_student.status, "Unknown"),
        # Student-specific attributes
        "IsMonk": django_student.is_monk,
        "PreferredStudyTime": (
            study_time_map.get(django_student.preferred_study_time)
            if django_student.preferred_study_time
            else None
        ),
        "IsTransferStudent": django_student.is_transfer_student,
    }


def legacy_student_to_django(legacy_record: dict[str, Any]) -> dict[str, Any]:
    """Map legacy Students table record to Django-compatible format.

    This is the reverse mapping for read operations.

    Args:
        legacy_record: Raw record from MSSQL Students table

    Returns:
        Dictionary with Django field names and values
    """
    # Reverse gender mapping
    # Legacy uses: M (Male), F (Female), Monk (special case)
    # WARNING: Legacy data is inconsistent! Could be "Monk", "monk", "MONK"
    # Django uses: M (Male), F (Female), N (Non-binary), X (Prefer not to say)
    # Django also has separate is_monk boolean field
    legacy_gender = str(legacy_record.get("Gender", "M")).strip()

    if legacy_gender.upper() == "MONK":
        # Monk in legacy (any casing) → is_monk=True, gender defaults to M
        django_gender = "M"
        is_monk = True
    else:
        # Normalize to uppercase for comparison
        gender_upper = legacy_gender.upper()
        gender_reverse_map = {
            "M": "M",
            "F": "F",
        }
        django_gender = gender_reverse_map.get(gender_upper, "M")
        # is_monk is stored in separate IsMonk field (if present)
        is_monk = legacy_record.get("IsMonk", False)

    # Reverse status mapping
    status_reverse_map = {
        "Active": "ACTIVE",
        "Inactive": "INACTIVE",
        "Graduated": "GRADUATED",
        "Dropped": "DROPPED",
        "Suspended": "SUSPENDED",
        "Transferred": "TRANSFERRED",
        "Frozen": "FROZEN",
        "Unknown": "UNKNOWN",
    }

    # Reverse study time mapping
    study_time_reverse_map = {
        "Morning": "morning",
        "Afternoon": "afternoon",
        "Evening": "evening",
    }

    # Get status value with default
    status_value = legacy_record.get("Status")
    if status_value is None:
        status_value = "Unknown"

    return {
        "student_id": legacy_record.get("StudentCode"),
        "legacy_student_id": legacy_record.get("StudentID"),
        "first_name": legacy_record.get("FirstName"),
        "last_name": legacy_record.get("LastName"),
        "middle_name": legacy_record.get("MiddleName"),
        "english_first_name": legacy_record.get("EnglishFirstName"),
        "english_last_name": legacy_record.get("EnglishLastName"),
        "date_of_birth": legacy_record.get("DateOfBirth"),
        "gender": django_gender,  # Uses monk-aware reverse mapping from above
        "email": legacy_record.get("Email"),
        "phone_number": legacy_record.get("PhoneNumber"),
        "enrollment_date": legacy_record.get("EnrollmentDate"),
        "status": status_reverse_map.get(status_value, "UNKNOWN"),
        "is_monk": is_monk,  # Extracted from Gender="Monk" or IsMonk field
        "preferred_study_time": study_time_reverse_map.get(
            legacy_record.get("PreferredStudyTime")
        ),
        "is_transfer_student": legacy_record.get("IsTransferStudent", False),
    }
