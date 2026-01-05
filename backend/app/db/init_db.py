from app.models.base import Base
from app.db.session import engine

# Import models so SQLAlchemy registers them
from app.models.user import User  # noqa: F401
from app.models.course import Course  # noqa: F401
from app.models.enrollment import Enrollment  # noqa: F401
from app.models.assignment import Assignment  # noqa: F401
from app.models.submission import Submission  # noqa: F401

def init_db():
    Base.metadata.create_all(bind=engine)
