from app.models.user import Base
from app.db.session import engine

def init_db():
    Base.metadata.create_all(bind=engine)
