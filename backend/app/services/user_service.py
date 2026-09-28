#Resonsability: user 

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserCreate
from app.configs.security import hash_pwd_tool

def create_user (db : Session, user_data: UserCreate) -> User:
    user = User(email = user_data.email, 
                password_hash = hash_pwd_tool(user_data.password),
                #role = user_data.role
                role = "USER")
    db.add(user)
    db.commit()
    db.refresh(user)

    return user

def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(
        select(User).where(User.email == email)
    )
