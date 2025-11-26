from dataclasses import dataclass
from typing import List
from datetime import datetime


@dataclass
class Student:
    student_id: str
    first_name: str
    last_name: str
    major: str


@dataclass
class Course:
    course_id: str
    course_name: str
    credits: int


@dataclass
class Recommendation:
    student: Student
    courses: List[Course]
    generated_at: datetime
