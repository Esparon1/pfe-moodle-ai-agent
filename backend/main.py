from fastapi import FastAPI, Depends
from sqlalchemy import text
from app.models.user import User
from sqlalchemy.orm import Session
from app.seed.seed import run_seed
from app.models.course import Course
from app.models.assignment import Assignment
from app.models.submission import Submission
from sqlalchemy import func, distinct
from app.models.enrollment import Enrollment


from app.db.deps import get_db
from app.db.init_db import init_db

app = FastAPI(title="PFE Mini-Moodle")

@app.on_event("startup")
def on_startup():
    init_db()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/db-check")
def db_check(db: Session = Depends(get_db)):
    value = db.execute(text("SELECT 1")).scalar_one()
    return {"db": "ok", "select_1": value}
@app.post("/seed")
def seed(db: Session = Depends(get_db)):
    run_seed(db)
    return {"seeded": True}
@app.get("/users")
def list_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return [
        {"id": u.id, "name": u.name, "role": u.role}
        for u in users
    ]
@app.get("/courses")
def list_courses(db: Session = Depends(get_db)):
    courses = db.query(Course).all()
    return [
        {"id": c.id, "code": c.code, "name": c.name}
        for c in courses
    ]
@app.get("/courses/{course_id}")
def course_detail(course_id: int, db: Session = Depends(get_db)):
    course = db.get(Course, course_id)
    if not course:
        return {"error": "Course not found"}

    assignments = (
        db.query(Assignment)
        .filter(Assignment.course_id == course_id)
        .all()
    )

    return {
        "id": course.id,
        "code": course.code,
        "name": course.name,
        "assignments": [
            {
                "id": a.id,
                "title": a.title,
                "due_date": a.due_date,
            }
            for a in assignments
        ],
    }
@app.get("/analytics/assignment/{assignment_id}/stats")
def assignment_stats(assignment_id: int, db: Session = Depends(get_db)):
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
@app.get("/analytics/course/{course_id}/summary")
def course_summary(course_id: int, db: Session = Depends(get_db)):
    course = db.get(Course, course_id)
    if not course:
        return {"error": "Course not found"}

    students = db.query(func.count(distinct(Enrollment.user_id))).filter(
        Enrollment.course_id == course_id
    ).scalar() or 0

    assignments_count = db.query(func.count(Assignment.id)).filter(
        Assignment.course_id == course_id
    ).scalar() or 0

    # submissions across all assignments in this course
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

    min_grade = db.query(func.min(Submission.grade)).join(
        Assignment, Submission.assignment_id == Assignment.id
    ).filter(
        Assignment.course_id == course_id,
        Submission.grade.isnot(None)
    ).scalar()

    max_grade = db.query(func.max(Submission.grade)).join(
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
        "min": float(min_grade) if min_grade is not None else None,
        "max": float(max_grade) if max_grade is not None else None,
    }

