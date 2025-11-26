"""Pydantic models for API requests/responses."""

from datetime import date, datetime

from pydantic import BaseModel, EmailStr, Field


class StudentCreateRequest(BaseModel):
    """Request model for creating a student in legacy database.

    This matches Django's StudentProfile and Person models.
    Fields are mapped from Django's schema to legacy MSSQL schema.
    """

    # Django-generated student_id (source of truth)
    student_id: int = Field(..., description="Django-generated student ID", gt=0)

    # Person fields (from Person model)
    first_name: str = Field(..., max_length=100, min_length=1)
    last_name: str = Field(..., max_length=100, min_length=1)
    middle_name: str | None = Field(None, max_length=100)
    english_first_name: str | None = Field(None, max_length=100)
    english_last_name: str | None = Field(None, max_length=100)
    date_of_birth: date
    gender: str = Field(..., pattern="^[MFNX]$")  # M, F, N, X
    email: EmailStr | None = None
    phone_number: str | None = Field(None, max_length=20)

    # StudentProfile fields
    is_monk: bool = False
    preferred_study_time: str | None = Field(
        None, pattern="^(morning|afternoon|evening)$"
    )
    is_transfer_student: bool = False
    status: str = "ACTIVE"
    enrollment_date: date | None = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
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
            ]
        }
    }


class StudentCreateResponse(BaseModel):
    """Response model for student creation."""

    success: bool
    student_id: int
    legacy_student_id: int | None = Field(
        None, description="Legacy database primary key (IDENTITY column)"
    )
    message: str


class LegacyStudentRecord(BaseModel):
    """Legacy database student record - matches actual MSSQL schema.

    Field names match MSSQL table column names exactly.
    """

    # Core Identity
    ID: str  # Primary student identifier (nvarchar(10))
    Name: str | None = None  # Full name (English)
    KName: str | None = None  # Khmer name

    # Personal Information
    BirthDate: datetime | None = None
    BirthPlace: str | None = None
    Gender: str | None = None

    # Contact Information
    Email: str | None = None
    MobilePhone: str | None = None
    HomePhone: str | None = None
    HomeAddress: str | None = None

    # Status
    Status: str | None = None
    Admitted: int | None = None  # 1/0 flag
    Deleted: int | None = None  # 1/0 flag

    # Program Information
    AdmissionDate: datetime | None = None
    AdmissionDateForUnder: datetime | None = None
    AdmissionDateForMaster: datetime | None = None
    SelectedProgram: str | None = None
    SelectedMajor: str | None = None
    SelectedFaculty: str | None = None

    # Enrollment Dates
    Firstenroll: datetime | None = None
    Lastenroll: datetime | None = None
    BAStartDate: datetime | None = None
    BAEndDate: datetime | None = None
    MAStartDate: datetime | None = None
    MAEndDate: datetime | None = None

    # Transfer Status
    Transfer: str | None = None

    # Audit Fields
    CreatedDate: datetime | None = None
    ModifiedDate: datetime | None = None


class LegacyAcademicClass(BaseModel):
    """Legacy database academic class record."""

    IPK: int  # Primary key from AcademicClasses table - stable identifier
    TermID: str | None = None
    Program: float | None = None
    Major: float | None = None
    GroupID: str | None = None
    CourseCode: str | None = None
    ClassID: str | None = None
    CourseTitle: str | None = None
    StNumber: float | None = None
    CourseType: str | None = None
    SchoolTime: str | None = None
    Subject: str | None = None
    NormalizedCourse: str | None = None
    NormalizedPart: str | None = None
    NormalizedSection: str | None = None
    NormalizedTOD: str | None = None
    CreatedDate: datetime | None = None
    ModifiedDate: datetime | None = None


class LegacyEnrollment(BaseModel):
    """Legacy database academic course taker (enrollment) record."""

    IPK: int  # Primary key from AcademicCourseTakers table - stable identifier
    ID: str | None = None  # Student ID
    ClassID: str | None = None
    RepeatNum: int | None = None
    LScore: float | None = None  # Lower score
    UScore: float | None = None  # Upper score
    Credit: int | None = None
    GradePoint: float | None = None
    TotalPoint: float | None = None
    Grade: str | None = None
    PreviousGrade: str | None = None
    Passed: int | None = None  # 1/0 flag
    Remarks: str | None = None
    RegisterMode: str | None = None
    Attendance: str | None = None
    AddTime: datetime | None = None
    LastUpdate: datetime | None = None
    NormalizedCourse: str | None = None
    NormalizedPart: str | None = None
    NormalizedSection: str | None = None


class StudentUpdateRequest(BaseModel):
    """Request model for updating student fields in legacy database.

    Only includes fields that exist in actual MSSQL Students table.
    All fields are optional - only provide fields you want to update.
    """

    Name: str | None = None
    KName: str | None = None
    Email: str | None = None
    MobilePhone: str | None = None
    HomePhone: str | None = None
    HomeAddress: str | None = None
    Status: str | None = None
    BirthDate: datetime | None = None
    BirthPlace: str | None = None
    Gender: str | None = None
    SelectedProgram: str | None = None
    SelectedMajor: str | None = None
    SelectedFaculty: str | None = None
    Transfer: str | None = None


class ErrorResponse(BaseModel):
    """Standard error response model."""

    detail: str
    timestamp: str | None = None


class HealthCheckResponse(BaseModel):
    """Health check response model."""

    status: str
    database: str
    timestamp: str
    version: str = "1.0.0"
