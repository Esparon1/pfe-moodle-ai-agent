from fastapi import APIRouter, Depends
from app.models.user import User
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/me", tags=["me"])

@router.get("")
def me(current_user: User = Depends(get_current_user)):
    return {"id": current_user.id, "name": current_user.name, "role": current_user.role}
