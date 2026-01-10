from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.seed.seed import run_seed
from app.models.user import User
from app.models.course import Course
from app.models.assignment import Assignment

router = APIRouter(tags=["platform"])

@router.post("/seed")
def seed(db: Session = Depends(get_db)):
    run_seed(db)
    return {"seeded": True}

@router.get("/users")
def list_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return [{"id": u.id, "name": u.name, "role": u.role} for u in users]

@router.get("/courses")
def list_courses(db: Session = Depends(get_db)):
    courses = db.query(Course).all()
    return [
        {"id": c.id, "code": c.code, "name": c.name, "instructor_id": c.instructor_id}
        for c in courses
    ]

@router.get("/courses/{course_id}")
def course_detail(course_id: int, db: Session = Depends(get_db)):
    course = db.get(Course, course_id)
    if not course:
        return {"error": "Course not found"}

    assignments = db.query(Assignment).filter(Assignment.course_id == course_id).all()

    return {
        "id": course.id,
        "code": course.code,
        "name": course.name,
        "instructor_id": course.instructor_id,
        "assignments": [
            {"id": a.id, "title": a.title, "due_date": a.due_date}
            for a in assignments
        ],
    }
