from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.models.user import User
from app.models.assignment import Assignment

from app.auth.dependencies import get_current_user
from app.auth.rbac import can_access_course
from app.services.analytics_service import assignment_stats, course_summary, student_progress

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/course/{course_id}/summary")
def course_summary_route(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not can_access_course(course_id, current_user, db):
        raise HTTPException(status_code=403, detail="Forbidden")
    return course_summary(db, course_id)

@router.get("/assignment/{assignment_id}/stats")
def assignment_stats_route(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    assignment = db.get(Assignment, assignment_id)
    if not assignment:
        return {"error": "Assignment not found"}

    if not can_access_course(assignment.course_id, current_user, db):
        raise HTTPException(status_code=403, detail="Forbidden")

    return assignment_stats(db, assignment_id)

@router.get("/student/{student_id}/progress")
def student_progress_route(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # student self-only
    if current_user.role == "STUDENT" and current_user.id != student_id:
        raise HTTPException(status_code=403, detail="Forbidden")

    # (si tu as déjà la restriction prof→étudiant, on l’ajoute ensuite)
    return student_progress(db, student_id)
