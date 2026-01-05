from datetime import datetime, timedelta
import random
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.assignment import Assignment
from app.models.submission import Submission

def run_seed(db: Session):
    # --- users
    admin = User(name="Admin", role="ADMIN")
    prof1 = User(name="Prof A", role="PROF")
    prof2 = User(name="Prof B", role="PROF")
    students = [User(name=f"Student {i:02d}", role="STUDENT") for i in range(1, 31)]

    db.add_all([admin, prof1, prof2, *students])
    db.flush()  # assigns IDs

    # --- courses
    courses = [
        Course(code="INF101", name="Intro au génie logiciel"),
        Course(code="DATA201", name="Data & BI Foundations"),
        Course(code="FIN305", name="Fintech Analytics"),
    ]
    db.add_all(courses)
    db.flush()

    # --- enrollments (all students enrolled in 2-3 courses)
    for s in students:
        for c in random.sample(courses, k=random.choice([2, 3])):
            db.add(Enrollment(user_id=s.id, course_id=c.id))

    # --- assignments (5 per course)
    now = datetime.utcnow()
    assignments = []
    for c in courses:
        for j in range(1, 6):
            a = Assignment(
                course_id=c.id,
                title=f"Devoir {j}",
                due_date=now + timedelta(days=7 * j),
            )
            assignments.append(a)
    db.add_all(assignments)
    db.flush()

    # --- submissions (realistic grades + some missing/late)
    enrollments = db.query(Enrollment).all()
    for e in enrollments:
        for a in [x for x in assignments if x.course_id == e.course_id]:
            r = random.random()
            if r < 0.12:
                # missing
                db.add(Submission(assignment_id=a.id, user_id=e.user_id, status="MISSING", grade=None, submitted_at=None))
            else:
                late = r < 0.22
                grade = max(0.0, min(100.0, random.gauss(75, 12)))
                submitted_at = a.due_date + timedelta(days=random.randint(1, 4)) if late else a.due_date - timedelta(days=random.randint(0, 3))
                db.add(Submission(
                    assignment_id=a.id,
                    user_id=e.user_id,
                    status="LATE" if late else "SUBMITTED",
                    grade=round(grade, 1),
                    submitted_at=submitted_at,
                ))

    db.commit()
