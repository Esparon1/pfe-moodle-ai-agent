from sqlalchemy.orm import Session
from sqlalchemy import func, distinct

from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.assignment import Assignment
from app.models.submission import Submission

def assignment_stats(db: Session, assignment_id: int) -> dict:
    total = db.query(Submission).filter(Submission.assignment_id == assignment_id).count()

    submitted = db.query(Submission).filter(
        Submission.assignment_id == assignment_id,
        Submission.status == "SUBMITTED"
    ).count()

    late = db.query(Submission).filter(
        Submission.assignment_id == assignment_id,
        Submission.status == "LATE"
    ).count()

    missing = db.query(Submission).filter(
        Submission.assignment_id == assignment_id,
        Submission.status == "MISSING"
    ).count()

    avg_grade = db.query(func.avg(Submission.grade)).filter(
        Submission.assignment_id == assignment_id,
        Submission.grade.isnot(None)
    ).scalar()

    min_grade = db.query(func.min(Submission.grade)).filter(
        Submission.assignment_id == assignment_id,
        Submission.grade.isnot(None)
    ).scalar()

    max_grade = db.query(func.max(Submission.grade)).filter(
        Submission.assignment_id == assignment_id,
        Submission.grade.isnot(None)
    ).scalar()

    return {
        "assignment_id": assignment_id,
        "total_records": total,
        "submitted": submitted,
        "late": late,
        "missing": missing,
        "average": round(float(avg_grade), 2) if avg_grade is not None else None,
        "min": float(min_grade) if min_grade is not None else None,
        "max": float(max_grade) if max_grade is not None else None,
    }

def course_summary(db: Session, course_id: int) -> dict:
    course = db.get(Course, course_id)
    if not course:
        return {"error": "Course not found"}

    students = db.query(func.count(distinct(Enrollment.user_id))).filter(
        Enrollment.course_id == course_id
    ).scalar() or 0

    assignments_count = db.query(func.count(Assignment.id)).filter(
        Assignment.course_id == course_id
    ).scalar() or 0

    total_records = db.query(func.count(Submission.id)).join(
        Assignment, Submission.assignment_id == Assignment.id
    ).filter(
        Assignment.course_id == course_id
    ).scalar() or 0

    submitted = db.query(func.count(Submission.id)).join(
        Assignment, Submission.assignment_id == Assignment.id
    ).filter(
        Assignment.course_id == course_id,
        Submission.status == "SUBMITTED"
    ).scalar() or 0

    late = db.query(func.count(Submission.id)).join(
        Assignment, Submission.assignment_id == Assignment.id
    ).filter(
        Assignment.course_id == course_id,
        Submission.status == "LATE"
    ).scalar() or 0

    missing = db.query(func.count(Submission.id)).join(
        Assignment, Submission.assignment_id == Assignment.id
    ).filter(
        Assignment.course_id == course_id,
        Submission.status == "MISSING"
    ).scalar() or 0

    avg_grade = db.query(func.avg(Submission.grade)).join(
        Assignment, Submission.assignment_id == Assignment.id
    ).filter(
        Assignment.course_id == course_id,
        Submission.grade.isnot(None)
    ).scalar()

    def rate(x: int, total: int) -> float:
        return round(x / total, 4) if total > 0 else 0.0

    return {
        "course": {"id": course.id, "code": course.code, "name": course.name},
        "students": int(students),
        "assignments": int(assignments_count),
        "total_submission_records": int(total_records),
        "submitted": int(submitted),
        "late": int(late),
        "missing": int(missing),
        "submission_rate": rate(submitted + late, total_records),
        "late_rate": rate(late, total_records),
        "missing_rate": rate(missing, total_records),
        "course_average": round(float(avg_grade), 2) if avg_grade is not None else None,
    }

def student_progress(db: Session, student_id: int) -> dict:
    total_records = db.query(func.count(Submission.id)).filter(
        Submission.user_id == student_id
    ).scalar() or 0

    submitted = db.query(func.count(Submission.id)).filter(
        Submission.user_id == student_id,
        Submission.status == "SUBMITTED"
    ).scalar() or 0

    late = db.query(func.count(Submission.id)).filter(
        Submission.user_id == student_id,
        Submission.status == "LATE"
    ).scalar() or 0

    missing = db.query(func.count(Submission.id)).filter(
        Submission.user_id == student_id,
        Submission.status == "MISSING"
    ).scalar() or 0

    avg_grade = db.query(func.avg(Submission.grade)).filter(
        Submission.user_id == student_id,
        Submission.grade.isnot(None)
    ).scalar()

    def rate(x: int, total: int) -> float:
        return round(x / total, 4) if total > 0 else 0.0

    return {
        "student_id": student_id,
        "total_submission_records": int(total_records),
        "submitted": int(submitted),
        "late": int(late),
        "missing": int(missing),
        "submission_rate": rate(submitted + late, total_records),
        "late_rate": rate(late, total_records),
        "missing_rate": rate(missing, total_records),
        "student_average": round(float(avg_grade), 2) if avg_grade is not None else None,
    }
