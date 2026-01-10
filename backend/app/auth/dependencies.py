from fastapi import Header, HTTPException, Depends
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.models.user import User

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
