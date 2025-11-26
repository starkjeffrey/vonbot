"""Unit tests for schema mappers (Django ↔ Legacy).

These tests verify the bidirectional mapping between Django's clean
architecture and the legacy MSSQL schema, including edge cases like:
- Monk gender handling
- Status code mapping
- Field name convention conversion (snake_case ↔ PascalCase)
- Default value handling
"""

from __future__ import annotations

from datetime import date

import pytest
from app.mappers import django_student_to_legacy, legacy_student_to_django
from app.models import StudentCreateRequest


@pytest.mark.unit
class TestDjangoToLegacyMapping:
    """Test mapping from Django schema to legacy MSSQL schema."""

    def test_basic_student_mapping(self):
        """Test standard student mapping with all fields."""
        request = StudentCreateRequest(
            student_id=12345,
            first_name="Sopheak",
            last_name="Chan",
            middle_name="Dara",
            english_first_name="Sopheak",
            english_last_name="Chan",
            date_of_birth=date(2000, 1, 15),
            gender="M",
            email="sopheak.chan@example.com",
            phone_number="+85512345678",
            is_monk=False,
            preferred_study_time="morning",
            is_transfer_student=False,
            status="ACTIVE",
            enrollment_date=date(2024, 1, 10),
        )

        result = django_student_to_legacy(request)

        # Verify field mapping
        assert result["StudentCode"] == 12345
        assert result["FirstName"] == "Sopheak"
        assert result["LastName"] == "Chan"
        assert result["MiddleName"] == "Dara"
        assert result["EnglishFirstName"] == "Sopheak"
        assert result["EnglishLastName"] == "Chan"
        assert result["DateOfBirth"] == date(2000, 1, 15)
        assert result["Gender"] == "M"
        assert result["Email"] == "sopheak.chan@example.com"
        assert result["PhoneNumber"] == "+85512345678"
        assert result["EnrollmentDate"] == date(2024, 1, 10)
        assert result["Status"] == "Active"  # ACTIVE → Active (title case)
        assert result["IsMonk"] is False
        assert result["PreferredStudyTime"] == "Morning"  # morning → Morning
        assert result["IsTransferStudent"] is False

    def test_monk_gender_mapping(self):
        """Test that is_monk=True sets Gender='Monk' in legacy."""
        request = StudentCreateRequest(
            student_id=67890,
            first_name="Bunthorn",
            last_name="Sao",
            date_of_birth=date(1998, 5, 20),
            gender="M",
            is_monk=True,  # This should override gender to "Monk"
        )

        result = django_student_to_legacy(request)

        assert result["Gender"] == "Monk"  # Overridden despite gender="M"
        assert result["IsMonk"] is True

    def test_female_student_mapping(self):
        """Test female student mapping."""
        request = StudentCreateRequest(
            student_id=11111,
            first_name="Sreymom",
            last_name="Keo",
            date_of_birth=date(2001, 3, 10),
            gender="F",
            is_monk=False,
        )

        result = django_student_to_legacy(request)

        assert result["Gender"] == "F"
        assert result["IsMonk"] is False

    def test_nonbinary_gender_defaults_to_male(self):
        """Test that non-binary (N) defaults to M in legacy (no equivalent)."""
        request = StudentCreateRequest(
            student_id=22222,
            first_name="Chamroeun",
            last_name="Lim",
            date_of_birth=date(1999, 7, 25),
            gender="N",  # Non-binary - no legacy equivalent
            is_monk=False,
        )

        result = django_student_to_legacy(request)

        assert result["Gender"] == "M"  # Default for unsupported gender

    def test_prefer_not_to_say_defaults_to_male(self):
        """Test that prefer not to say (X) defaults to M in legacy."""
        request = StudentCreateRequest(
            student_id=33333,
            first_name="Veasna",
            last_name="Prak",
            date_of_birth=date(2000, 11, 5),
            gender="X",  # Prefer not to say
            is_monk=False,
        )

        result = django_student_to_legacy(request)

        assert result["Gender"] == "M"  # Default for unsupported gender

    def test_status_mapping_all_values(self):
        """Test all status code mappings."""
        status_tests = [
            ("ACTIVE", "Active"),
            ("INACTIVE", "Inactive"),
            ("GRADUATED", "Graduated"),
            ("DROPPED", "Dropped"),
            ("SUSPENDED", "Suspended"),
            ("TRANSFERRED", "Transferred"),
            ("FROZEN", "Frozen"),
            ("UNKNOWN", "Unknown"),
            ("INVALID_STATUS", "Unknown"),  # Unknown status defaults to "Unknown"
        ]

        for django_status, expected_legacy in status_tests:
            request = StudentCreateRequest(
                student_id=12345,
                first_name="Test",
                last_name="Student",
                date_of_birth=date(2000, 1, 1),
                gender="M",
                status=django_status,
            )
            result = django_student_to_legacy(request)
            assert result["Status"] == expected_legacy, (
                f"Failed for status: {django_status}"
            )

    def test_study_time_mapping(self):
        """Test study time preference mapping."""
        study_time_tests = [
            ("morning", "Morning"),
            ("afternoon", "Afternoon"),
            ("evening", "Evening"),
            (None, None),  # Null handling
        ]

        for django_time, expected_legacy in study_time_tests:
            request = StudentCreateRequest(
                student_id=12345,
                first_name="Test",
                last_name="Student",
                date_of_birth=date(2000, 1, 1),
                gender="M",
                preferred_study_time=django_time,
            )
            result = django_student_to_legacy(request)
            assert result["PreferredStudyTime"] == expected_legacy

    def test_optional_fields_none(self):
        """Test mapping with all optional fields set to None."""
        request = StudentCreateRequest(
            student_id=44444,
            first_name="Minimal",
            last_name="Student",
            date_of_birth=date(2000, 1, 1),
            gender="M",
            # All optional fields omitted (None)
            middle_name=None,
            english_first_name=None,
            english_last_name=None,
            email=None,
            phone_number=None,
            preferred_study_time=None,
            enrollment_date=None,  # Should default to today
        )

        result = django_student_to_legacy(request)

        assert result["MiddleName"] is None
        assert result["EnglishFirstName"] is None
        assert result["EnglishLastName"] is None
        assert result["Email"] is None
        assert result["PhoneNumber"] is None
        assert result["PreferredStudyTime"] is None
        assert result["EnrollmentDate"] == date.today()  # Auto-filled


@pytest.mark.unit
class TestLegacyToDjangoMapping:
    """Test mapping from legacy MSSQL schema to Django schema."""

    def test_basic_legacy_to_django(self, sample_legacy_record):
        """Test standard legacy record to Django mapping."""
        result = legacy_student_to_django(sample_legacy_record)

        assert result["student_id"] == 12345
        assert result["legacy_student_id"] == 999
        assert result["first_name"] == "Sopheak"
        assert result["last_name"] == "Chan"
        assert result["gender"] == "M"
        assert result["email"] == "sopheak.chan@example.com"
        assert result["status"] == "ACTIVE"  # Active → ACTIVE
        assert result["is_monk"] is False
        assert result["preferred_study_time"] == "morning"  # Morning → morning

    def test_monk_legacy_to_django(self, sample_legacy_monk_record):
        """Test monk record with Gender='Monk' converts correctly."""
        result = legacy_student_to_django(sample_legacy_monk_record)

        assert result["gender"] == "M"  # Monk → M (default gender)
        assert result["is_monk"] is True  # Extracted from Gender='Monk'

    def test_monk_casing_variations(self):
        """Test that Gender='Monk' works regardless of casing."""
        casing_tests = ["Monk", "monk", "MONK", "MoNk"]

        for monk_value in casing_tests:
            legacy_record = {
                "StudentID": 777,
                "StudentCode": 55555,
                "FirstName": "Test",
                "LastName": "Monk",
                "DateOfBirth": date(2000, 1, 1),
                "Gender": monk_value,
                "Status": "Active",
                "IsMonk": True,
            }
            result = legacy_student_to_django(legacy_record)
            assert result["is_monk"] is True, f"Failed for Gender='{monk_value}'"
            assert result["gender"] == "M"

    def test_status_reverse_mapping(self):
        """Test all status reverse mappings."""
        status_tests = [
            ("Active", "ACTIVE"),
            ("Inactive", "INACTIVE"),
            ("Graduated", "GRADUATED"),
            ("Dropped", "DROPPED"),
            ("Suspended", "SUSPENDED"),
            ("Transferred", "TRANSFERRED"),
            ("Frozen", "FROZEN"),
            ("Unknown", "UNKNOWN"),
            (None, "UNKNOWN"),  # None defaults to UNKNOWN
        ]

        for legacy_status, expected_django in status_tests:
            legacy_record = {
                "StudentID": 111,
                "StudentCode": 12345,
                "FirstName": "Test",
                "LastName": "Student",
                "DateOfBirth": date(2000, 1, 1),
                "Gender": "M",
                "Status": legacy_status,
                "IsMonk": False,
            }
            result = legacy_student_to_django(legacy_record)
            assert result["status"] == expected_django, (
                f"Failed for status: {legacy_status}"
            )

    def test_missing_optional_fields(self):
        """Test handling of missing optional fields in legacy record."""
        minimal_record = {
            "StudentID": 222,
            "StudentCode": 66666,
            "FirstName": "Minimal",
            "LastName": "Record",
            "DateOfBirth": date(2000, 1, 1),
            "Gender": "F",
            "Status": "Active",
            # Missing: MiddleName, English names, email, phone, etc.
        }

        result = legacy_student_to_django(minimal_record)

        assert result["student_id"] == 66666
        assert result["first_name"] == "Minimal"
        assert result["gender"] == "F"
        assert result["middle_name"] is None
        assert result["email"] is None
        assert result["is_monk"] is False  # Default when IsMonk missing


@pytest.mark.unit
class TestRoundTripMapping:
    """Test bidirectional mapping consistency."""

    def test_roundtrip_standard_student(self):
        """Test Django → Legacy → Django produces consistent data."""
        original_request = StudentCreateRequest(
            student_id=77777,
            first_name="Roundtrip",
            last_name="Test",
            date_of_birth=date(2000, 6, 15),
            gender="F",
            email="roundtrip@example.com",
            status="ACTIVE",
            is_monk=False,
            preferred_study_time="afternoon",
        )

        # Django → Legacy
        legacy_data = django_student_to_legacy(original_request)

        # Simulate legacy database record (add StudentID)
        legacy_data["StudentID"] = 999

        # Legacy → Django
        django_data = legacy_student_to_django(legacy_data)

        # Verify key fields match
        assert django_data["student_id"] == original_request.student_id
        assert django_data["first_name"] == original_request.first_name
        assert django_data["last_name"] == original_request.last_name
        assert django_data["gender"] == original_request.gender
        assert django_data["status"] == original_request.status
        assert django_data["is_monk"] == original_request.is_monk
        assert (
            django_data["preferred_study_time"] == original_request.preferred_study_time
        )

    def test_roundtrip_monk_student(self):
        """Test monk student roundtrip mapping."""
        original_request = StudentCreateRequest(
            student_id=88888,
            first_name="Monk",
            last_name="Roundtrip",
            date_of_birth=date(1995, 3, 20),
            gender="M",
            is_monk=True,
            status="ACTIVE",
        )

        # Django → Legacy
        legacy_data = django_student_to_legacy(original_request)
        assert legacy_data["Gender"] == "Monk"  # Monk override

        # Simulate legacy database record
        legacy_data["StudentID"] = 888

        # Legacy → Django
        django_data = legacy_student_to_django(legacy_data)

        # Verify monk flag preserved
        assert django_data["is_monk"] is True
        assert django_data["gender"] == "M"  # Extracted from Monk
