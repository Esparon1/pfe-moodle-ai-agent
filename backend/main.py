from fastapi import Header,HTTPException,FastAPI, Depends
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

#dependencies 
def get_current_user(
    x_user_id: int | None = Header(default=None, alias="X-USER-ID"),
    db: Session = Depends(get_db),
) -> User:
    if x_user_id is None:
        raise HTTPException(status_code=401, detail="Missing X-USER-ID header")

    user = db.get(User, x_user_id)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid user")
    return user

def can_access_course(course_id: int, current_user: User, db: Session) -> bool:
    if current_user.role == "ADMIN":
        return True

    course = db.get(Course, course_id)
    if not course:
        return False

    if current_user.role == "PROF":
        return course.instructor_id == current_user.id

    # STUDENT
    return db.query(Enrollment).filter(
        Enrollment.course_id == course_id,
        Enrollment.user_id == current_user.id
    ).first() is not None
def prof_can_access_student(student_id: int, prof_id: int, db: Session) -> bool:
    # Find if student is enrolled in any course taught by this prof
    return db.query(Enrollment).join(
        Course, Enrollment.course_id == Course.id
    ).filter(
        Enrollment.user_id == student_id,
        Course.instructor_id == prof_id
    ).first() is not None

#events 
@app.on_event("startup")
def on_startup():
    init_db()

#routes
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
        {"id": c.id, "code": c.code, "name": c.name,"instructor_id": c.instructor_id}
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
def assignment_stats(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    assignment = db.get(Assignment, assignment_id)
    if not assignment:
        return {"error": "Assignment not found"}

    if not can_access_course(assignment.course_id, current_user, db):
        raise HTTPException(status_code=403, detail="Forbidden")
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
def course_summary(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    course = db.get(Course, course_id)
    if not course:
        return {"error": "Course not found"}
    if not can_access_course(course_id, current_user, db):
        raise HTTPException(status_code=403, detail="Forbidden")
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
@app.get("/analytics/student/{student_id}/progress")
def student_progress(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
 ):
        # STUDENT: only self
    if current_user.role == "STUDENT" and current_user.id != student_id:
        raise HTTPException(status_code=403, detail="Forbidden: students can only access their own stats")
    
     # PROF: only students in prof's courses
    if current_user.role == "PROF" and not prof_can_access_student(student_id, current_user.id, db):
        raise HTTPException(status_code=403, detail="Forbidden")
    
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

