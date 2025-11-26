# Curriculum Requirements CSV

## Overview

The `curriculum_requirements.csv` file defines which courses are required for each academic major. This simplified format makes it easy to view and edit course requirements directly.

## File Format

```csv
course_code,BAD,THM,FIN,TES,INT
ACCT-300,X,,X,,
ACCT-310,X,X,X,,
...
```

### Columns

- **course_code**: The course code (e.g., `ACCT-300`, `ENGL-110`)
- **BAD**: Business Administration major (mark with `X` if required)
- **THM**: Tourism & Hospitality major (mark with `X` if required)
- **FIN**: Finance major (mark with `X` if required)
- **TES**: TESOL major (mark with `X` if required)
- **INT**: International Relations major (mark with `X` if required)

### Major Mappings

| Code | Full Name                  | BatchIDForMaster Prefix |
|------|----------------------------|-------------------------|
| BAD  | Business Administration    | BAD-*                   |
| THM  | Tourism & Hospitality      | THM-*                   |
| FIN  | Finance                    | FIN-*                   |
| TES  | TESOL                      | TES-*                   |
| INT  | International Relations    | INT-*                   |

## Current Statistics

- **Total courses**: 123
- **BAD requirements**: 42 courses
- **THM requirements**: 42 courses
- **FIN requirements**: 42 courses
- **TES requirements**: 42 courses
- **INT requirements**: 42 courses

## How to Edit

### Adding a New Course

1. Open `curriculum_requirements.csv` in a text editor or spreadsheet program
2. Add a new row with the course code
3. Mark with `X` in the columns for majors that require this course
4. Save the file

Example - adding `NEW-101` required for BAD and FIN:
```csv
NEW-101,X,,X,,
```

### Removing a Course

1. Find the row with the course code
2. Delete the entire row
3. Save the file

### Changing Requirements

1. Find the row with the course code
2. Add or remove `X` marks in the appropriate major columns
3. Save the file

Example - making `MATH-101` no longer required for THM:
```csv
# Before
MATH-101,X,X,X,X,X

# After
MATH-101,X,,X,X,X
```

## Editing in Excel/Google Sheets

The CSV can be opened in Excel or Google Sheets for easier editing:

1. Open the file in your spreadsheet program
2. Make changes using the grid interface
3. Export/Save as CSV (not XLSX!)
4. Ensure the file is saved as `curriculum_requirements.csv`

**Important**: Always save as CSV format, not Excel format (.xlsx)

## How It Works

When VonBot runs, it:
1. Loads this CSV file
2. Extracts the student's major prefix from their `BatchIDForMaster` (e.g., `TES-53E` → `TES`)
3. Finds all courses with `X` in that major's column
4. Checks the student's transcript to see which they've already completed
5. Returns the list of courses they still need

## Validation

After editing, you can test the file loads correctly:

```bash
source .venv/bin/activate
python3 << 'EOF'
from logic.course_matching import load_requirements

reqs = load_requirements()
print(f"✓ Loaded {len(reqs)} courses successfully")

# Count requirements per major
for major in ['BAD', 'THM', 'FIN', 'TES', 'INT']:
    count = len(reqs[reqs[major] == 'X'])
    print(f"  {major}: {count} courses")
EOF
```

## Backup

The original complex CSV file has been backed up to:
`curriculum_canonical_requirements_majors_1-6.csv.backup`

## Migration Notes

This simplified CSV was generated on 2024-11-26 from the original `curriculum_canonical_requirements_majors_1-6.csv` which contained:
- 217 rows with extensive metadata
- Multiple redundant columns (sequence_number, description, is_active, notes, effective_term_id, end_term_id, required_course_id)
- Complex parsing requirements

The simplified version contains only the essential data needed for course matching.

## Common Courses

Some courses are required across all majors:
- `ANTH-102` - Cultural Anthropology
- `ARIL-210` - Academic Research: Information Literacy
- `COMP-210` - Introduction to Computers
- `ENGL-110` - College English I
- `ENGL-120` - College English II
- `HF-101` - Health Education I
- `HIST-230` - History of Cambodia
- `KHMR-210` - Introduction to Khmer Studies
- `MATH-101` - College Algebra
- `PHIL-110` - Logic & Critical Thinking
- `PHIL-312` - Introduction to Ethics
- `POL-101` - Introduction to Political Science
- `PSYC-102` - Personal Growth and Development
- `SOC-110` - Gender Studies

## Support

If you have questions about editing this file, refer to:
- This README
- `WARP.md` - Main project documentation
- `logic/course_matching.py` - Code that uses this CSV

---

**Last Updated**: November 26, 2024
**Version**: 2.0 (Simplified)
