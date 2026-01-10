from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.user import User
from app.models.course import Course
from app.models.enrollment import Enrollment

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
