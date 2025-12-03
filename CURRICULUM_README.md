# Curriculum Requirements CSV

## Overview

The `curriculum_requirements2.csv` file defines which courses are required for each academic major, including course titles for display throughout the application. This simplified tab-separated format makes it easy to view and edit course requirements directly.

## File Format

The file uses **tab-separated** format (TSV) with quoted course titles:

```tsv
course_code	BAD	THM	FIN	TES	INT	course_title
ACCT-300	X		X			"Intro to Pub Policy & Admin"
ACCT-310	X	X	X			"English Eff Comm"
...
```

### Columns

- **course_code**: The course code (e.g., `ACCT-300`, `ENGL-110`)
- **BAD**: Business Administration major (mark with `X` if required)
- **THM**: Tourism & Hospitality major (mark with `X` if required)
- **FIN**: Finance major (mark with `X` if required)
- **TES**: TESOL major (mark with `X` if required)
- **INT**: International Relations major (mark with `X` if required)
- **course_title**: The full course title enclosed in double quotes (e.g., `"Logic & Crit Thinking"`)

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

1. Open `curriculum_requirements2.csv` in a text editor or spreadsheet program
2. Add a new row with the course code, major markers, and course title
3. Mark with `X` in the columns for majors that require this course
4. Enclose the course title in double quotes
5. Save the file

Example - adding `NEW-101` required for BAD and FIN:
```tsv
NEW-101	X		X			"Introduction to New Subject"
```

**Important**: Course titles MUST be enclosed in double quotes to handle special characters like apostrophes, ampersands, and colons.

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

The TSV file can be opened in Excel or Google Sheets for easier editing:

1. Open the file in your spreadsheet program (it will recognize tab-separated format)
2. Make changes using the grid interface
3. Ensure course titles remain in quotes
4. Export/Save as Tab-delimited text (.txt or .tsv)
5. Rename the file to `curriculum_requirements2.csv`

**Important**: Always save as tab-separated format, not Excel format (.xlsx) or comma-separated (.csv)

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

## Migration Notes

**Version 2.0** (curriculum_requirements2.csv) - Current format with course titles:
- Tab-separated format for better handling of special characters
- Added course_title column for display throughout the application
- Quoted course titles to handle apostrophes, ampersands, slashes, and colons
- Generated from Version 1.0 with course titles added

**Version 1.0** (curriculum_requirements.csv) - Obsolete:
- Comma-separated format
- No course titles
- Generated on 2024-11-26 from original `curriculum_canonical_requirements_majors_1-6.csv`

The original complex CSV contained 217 rows with extensive metadata, multiple redundant columns (sequence_number, description, is_active, notes, effective_term_id, end_term_id, required_course_id), and complex parsing requirements.

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
