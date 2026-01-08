from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer,ForeignKey
from .base import Base

class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)  
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    instructor_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
