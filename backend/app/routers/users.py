from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.user import UserResponse
from app.configs.dependencies import get_current_user

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.get("/", response_model=list[UserResponse])
def get_users(db: Session = Depends(get_db)):
    users = db.scalars(
        select(User)
    ).all()

    return users

@router.get(
    "/me",
    response_model=UserResponse,
)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user