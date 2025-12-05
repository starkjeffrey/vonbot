#!/usr/bin/env python3
"""
Match academic.canonicalrequirement.json to curriculum_requirements2.csv

Uses curriculum.course.json to map course IDs to course codes,
then compares requirements between Django fixture and CSV.
"""

import json
import pandas as pd
from collections import defaultdict

def load_course_mapping(filepath: str) -> dict:
    """Load course ID → code mapping from curriculum.course.json"""
    with open(filepath, 'r') as f:
        data = json.load(f)

    mapping = {}
    for record in data:
        if record.get('model') != 'curriculum.course':
            continue
        pk = record['pk']
        code = record['fields'].get('code', '')
        mapping[pk] = code

    return mapping


def load_json_requirements(filepath: str, course_mapping: dict) -> dict:
    """Load and parse the Django fixture, converting course IDs to codes."""
    with open(filepath, 'r') as f:
        data = json.load(f)

    majors = defaultdict(lambda: {'courses': set(), 'course_ids': set()})

    for record in data:
        if record.get('model') != 'academic.canonicalrequirement':
            continue

        fields = record['fields']
        if fields.get('is_deleted') or not fields.get('is_active'):
            continue

        major_id = fields['major']
        course_id = fields['required_course']

        # Convert ID to code
        course_code = course_mapping.get(course_id, f"UNKNOWN-{course_id}")

        majors[major_id]['course_ids'].add(course_id)
        majors[major_id]['courses'].add(course_code)

    return dict(majors)


def load_csv_requirements(filepath: str) -> dict:
    """Load and parse the CSV file."""
    df = pd.read_csv(filepath, sep='\t')

    majors = {}
    major_cols = ['BAD', 'THM', 'FIN', 'TES', 'INT']

    for col in major_cols:
        if col in df.columns:
            courses = set(df[df[col] == 'X']['course_code'].tolist())
            majors[col] = courses

    return majors


def find_best_match(json_courses: set, csv_reqs: dict) -> tuple:
    """Find the best matching CSV major for a set of JSON courses."""
    best_match = None
    best_overlap = 0
    best_jaccard = 0

    for code, csv_courses in csv_reqs.items():
        overlap = len(json_courses & csv_courses)
        union = len(json_courses | csv_courses)
        jaccard = overlap / union if union > 0 else 0

        if jaccard > best_jaccard:
            best_jaccard = jaccard
            best_overlap = overlap
            best_match = code

    return best_match, best_overlap, best_jaccard


def analyze_and_match():
    """Analyze both files and match majors."""

    print("=" * 80)
    print("REQUIREMENTS MATCHING ANALYSIS")
    print("=" * 80)

    # Load data
    course_mapping = load_course_mapping('curriculum.course.json')
    print(f"\n✅ Loaded {len(course_mapping)} courses from curriculum.course.json")

    json_reqs = load_json_requirements('academic.canonicalrequirement.json', course_mapping)
    print(f"✅ Loaded {len(json_reqs)} majors from academic.canonicalrequirement.json")

    csv_reqs = load_csv_requirements('curriculum_requirements2.csv')
    print(f"✅ Loaded {len(csv_reqs)} majors from curriculum_requirements2.csv")

    # Deduce mapping
    print("\n" + "=" * 80)
    print("MAJOR MAPPING (JSON PK → CSV Code)")
    print("=" * 80)

    mapping = {}
    for major_id in sorted(json_reqs.keys()):
        json_courses = json_reqs[major_id]['courses']
        best_match, overlap, jaccard = find_best_match(json_courses, csv_reqs)
        mapping[major_id] = best_match

        csv_count = len(csv_reqs.get(best_match, set()))
        json_count = len(json_courses)

        print(f"\n  Major {major_id} → {best_match}")
        print(f"    JSON courses: {json_count}, CSV courses: {csv_count}")
        print(f"    Overlap: {overlap}, Jaccard similarity: {jaccard:.1%}")

    # Detailed comparison
    print("\n" + "=" * 80)
    print("DETAILED COMPARISON BY MAJOR")
    print("=" * 80)

    for major_id in sorted(json_reqs.keys()):
        csv_code = mapping[major_id]
        json_courses = json_reqs[major_id]['courses']
        csv_courses = csv_reqs.get(csv_code, set())

        in_json_only = json_courses - csv_courses
        in_csv_only = csv_courses - json_courses
        in_both = json_courses & csv_courses

        print(f"\n{'='*60}")
        print(f"Major {major_id} ({csv_code})")
        print(f"{'='*60}")
        print(f"  ✅ In BOTH ({len(in_both)}): {sorted(in_both)[:15]}{'...' if len(in_both) > 15 else ''}")

        if in_json_only:
            print(f"  ⚠️  In JSON only ({len(in_json_only)}): {sorted(in_json_only)}")
        if in_csv_only:
            print(f"  ⚠️  In CSV only ({len(in_csv_only)}): {sorted(in_csv_only)}")

    # Summary of discrepancies
    print("\n" + "=" * 80)
    print("SUMMARY OF DISCREPANCIES")
    print("=" * 80)

    total_json_only = set()
    total_csv_only = set()

    for major_id in sorted(json_reqs.keys()):
        csv_code = mapping[major_id]
        json_courses = json_reqs[major_id]['courses']
        csv_courses = csv_reqs.get(csv_code, set())

        in_json_only = json_courses - csv_courses
        in_csv_only = csv_courses - json_courses

        total_json_only.update(in_json_only)
        total_csv_only.update(in_csv_only)

    print(f"\n  Courses in JSON but missing from CSV: {len(total_json_only)}")
    if total_json_only:
        for course in sorted(total_json_only):
            print(f"    - {course}")

    print(f"\n  Courses in CSV but missing from JSON: {len(total_csv_only)}")
    if total_csv_only:
        for course in sorted(total_csv_only):
            print(f"    - {course}")

    # Final mapping table
    print("\n" + "=" * 80)
    print("FINAL MAPPING TABLE")
    print("=" * 80)
    print("\n  JSON Major PK | CSV Major Code | Courses Match")
    print("  " + "-" * 50)
    for major_id in sorted(mapping.keys()):
        csv_code = mapping[major_id]
        json_courses = json_reqs[major_id]['courses']
        csv_courses = csv_reqs.get(csv_code, set())
        match_status = "✅ EXACT" if json_courses == csv_courses else "⚠️ DIFF"
        print(f"  {major_id:14} | {csv_code:14} | {match_status}")

    return mapping, json_reqs, csv_reqs


if __name__ == "__main__":
    analyze_and_match()
