# Legacy MSSQL Database Schema

**Database:** New_PUCDB
**Server:** 96.9.90.64:1500
**Version:** MSSQL 2012

---

## Students Table

Primary student records table.

**Primary Key:** `ID` (nvarchar(10), NOT NULL)

### Core Identity Fields
| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| ID | nvarchar(10) | NO | **Primary student identifier** |
| UI | nvarchar(100) | YES | User interface identifier |
| PW | nvarchar(10) | YES | Password |
| Name | nvarchar(100) | YES | Full name (English) |
| KName | nvarchar(100) | YES | Khmer name |

### Personal Information
| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| BirthDate | datetime | YES | Date of birth |
| BirthPlace | nvarchar(50) | YES | Place of birth |
| Gender | nvarchar(30) | YES | Gender |
| MaritalStatus | nvarchar(30) | YES | Marital status |
| Nationality | nvarchar(50) | YES | Nationality |

### Contact Information
| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| HomeAddress | nvarchar(250) | YES | Home address |
| HomePhone | nvarchar(50) | YES | Home phone |
| Email | nvarchar(50) | YES | Personal email |
| MobilePhone | nvarchar(50) | YES | Mobile phone |
| SchoolEmail | varchar(100) | YES | School email |

### Employment Information
| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| EmploymentPlace | nvarchar(200) | YES | Place of employment |
| Position | nvarchar(150) | YES | Job position |

### Family/Emergency Contact
| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| FatherName | nvarchar(50) | YES | Father's name |
| SpouseName | nvarchar(50) | YES | Spouse's name |
| Emg_ContactPerson | nvarchar(50) | YES | Emergency contact person |
| Relationship | nvarchar(50) | YES | Relationship to emergency contact |
| ContactPersonAddress | nvarchar(250) | YES | Emergency contact address |
| ContactPersonPhone | nvarchar(30) | YES | Emergency contact phone |

### Educational Background - High School
| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| HighSchoolProgram_School | nvarchar(150) | YES | High school name |
| HighSchoolProgram_Province | nvarchar(100) | YES | Province |
| HighSchoolProgram_Year | int | YES | Year graduated |
| HighSchoolProgram_Diploma | char(10) | YES | Diploma type |

### Educational Background - English Program
| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| EnglishProgram_School | nvarchar(150) | YES | English school |
| EnglishProgram_Level | nvarchar(50) | YES | Level achieved |
| EnglishProgram_Year | int | YES | Year completed |

### Educational Background - Less Than Four Year Program
| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| LessThanFourYearProgram_School | nvarchar(150) | YES | School name |
| LessThanFourYearProgram_Year | nvarchar(50) | YES | Year completed |

### Educational Background - Four Year Program (BA)
| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| FourYearProgram_School | nvarchar(150) | YES | School name |
| FourYearProgram_Degree | nvarchar(50) | YES | Degree type |
| FourYearProgram_Major | nvarchar(100) | YES | Major |
| FourYearProgram_Year | int | YES | Year completed |

### Educational Background - Graduate Program (MA)
| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| GraduateProgram_School | nvarchar(100) | YES | School name |
| GraduateProgram_Degree | nvarchar(50) | YES | Degree type |
| GraduateProgram_Major | nvarchar(100) | YES | Major |
| GraduateProgram_Year | int | YES | Year completed |

### Educational Background - Post Graduate Program (PhD)
| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| PostGraduateProgram_School | nvarchar(150) | YES | School name |
| PostGraduateProgram_Degree | nvarchar(100) | YES | Degree type |
| PostGraduateProgram_Major | nvarchar(100) | YES | Major |
| PostGraduateProgram_Year | int | YES | Year completed |

### PUCSR Program Information
| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| CurrentProgram | nvarchar(50) | YES | Current program |
| SelProgram | float | YES | Selected program ID |
| SelectedProgram | nvarchar(100) | YES | Selected program name |
| SelMajor | float | YES | Selected major ID |
| SelectedMajor | nvarchar(100) | YES | Selected major name |
| SelFaculty | float | YES | Selected faculty ID |
| SelectedFaculty | nvarchar(150) | YES | Selected faculty name |
| SelectedDegreeType | nvarchar(100) | YES | Degree type |

### Admission & Enrollment Dates
| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| AdmissionDate | datetime | YES | General admission date |
| AdmissionDateForUnder | datetime | YES | BA admission date |
| AdmissionDateForMaster | datetime | YES | MA admission date |
| AdmissionDateForDoctor | datetime | YES | PhD admission date |
| Firstenroll | datetime | YES | First enrollment (any) |
| Firstenroll_Lang | datetime | YES | First language enrollment |
| Firstenroll_BA | datetime | YES | First BA enrollment |
| Firstenroll_MA | datetime | YES | First MA enrollment |
| Lastenroll | datetime | YES | Last enrollment |
| LanguageStartDate | datetime | YES | Language program start |
| LanguageEndDate | datetime | YES | Language program end |
| BAStartDate | datetime | YES | BA start date |
| BAEndDate | datetime | YES | BA end date |
| MAStartDate | datetime | YES | MA start date |
| MAEndDate | datetime | YES | MA end date |

### Transfer Credit Information
| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| PreviousDegree | nvarchar(200) | YES | Previous degree |
| PreviousInstitution | nvarchar(200) | YES | Previous institution |
| YearAwarded | nvarchar(10) | YES | Year awarded |
| OtherCreditTransferInstitution | nvarchar(200) | YES | Transfer institution |
| DegreeAwarded | nvarchar(150) | YES | Degree awarded |
| Transfer | nvarchar(25) | YES | Transfer status |

### Graduation Information
| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| GraduationDate | datetime | YES | General graduation date |
| BAGradDate | datetime | YES | BA graduation date |
| MAGradDate | datetime | YES | MA graduation date |

### Term & Payment Information
| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| FirstTerm | nvarchar(50) | YES | First enrolled term |
| PaidTerm | char(50) | YES | Paid term |
| LastPaidTerm | nvarchar(50) | YES | Last paid term |
| LastPaidStartDate | datetime | YES | Last paid term start date |

### Batch & Group Information
| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| BatchID | nvarchar(20) | YES | General batch ID |
| BatchIDForUnder | nvarchar(20) | YES | BA batch ID |
| BatchIDForMaster | nvarchar(20) | YES | MA batch ID |
| BatchIDForDoctor | nvarchar(20) | YES | PhD batch ID |
| GroupID | char(20) | YES | Group ID |
| intGroupID | float | YES | Integer group ID |
| Color | nvarchar(20) | YES | Color code |

### Status & Administrative Fields
| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| Admitted | int | YES | Admitted flag (1/0) |
| Deleted | int | YES | Deleted flag (1/0) |
| Status | varchar(15) | YES | Student status |
| Notes | varchar(255) | YES | Administrative notes |
| IPK | int | NO | IPK identifier |

### Audit Fields
| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| CreatedDate | datetime | YES | Record creation date |
| ModifiedDate | datetime | YES | Last modification date |

---

## Key Tables

Total: 122 tables in database

### Academic Tables
- **Students** - Student records (primary)
- **AcademicClasses** - Academic course sections
- **AcademicCourseTakers** - Academic enrollments
- **Courses** - Course catalog
- **GradeSheetHeader** - Grade sheets
- **GradingSystem** - Grading rubrics

### Language Program Tables
- **LangClasses** - Language course sections
- **LangCourseTakers** - Language enrollments
- **LangCourseTakerGrades** - Language grades
- **LangSubjects** - Language courses
- **LangProgLevSubs** - Language program levels

### Financial Tables
- **Receipt_Headers** - Payment receipts
- **Receipt_Items** - Receipt line items
- **Fees** - Fee structures
- **Prices** - Pricing information
- **Scholarships** - Scholarship records
- **Deductions** - Payment deductions

### Administrative Tables
- **Terms** - Academic terms
- **Teachers** - Faculty records
- **Rooms** - Room assignments
- **Users** - System users
- **GroupIDs** - Student cohorts

---

## Notes

1. **Primary Key:** The `ID` field (not `StudentCode`) is the primary identifier
2. **Nullable Fields:** Most fields are nullable (YES) - handle NULL values
3. **Date Fields:** Use `datetime` type - may be NULL
4. **Float IDs:** Several ID fields use `float` type (SelProgram, SelMajor, etc.)
5. **Encoding:** Uses `nvarchar` for Unicode support (Khmer text)
6. **Legacy Structure:** Contains many denormalized fields and duplicate data