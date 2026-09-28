from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.user import UserCreate, UserResponse, Token
#import creation user service from service folder
from app.services.user_service import create_user, get_user_by_email
from app.services.auth_service import auth_user, create_user_access_token


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)

#set the POST API for registration
@router.post(
    "/register",
    response_model=UserResponse,
)
def register(user_data: UserCreate, db: Session = Depends(get_db)): 
    #check if the user already exist
    existing_user = get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered",
        )

    return create_user(
        db,
        user_data,
    )

@router.post(
    "/login",
    response_model= Token
)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    #user = auth_user(db,form_data.email, form_data.password)
    user = auth_user(db,form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password",
        )

    access_token = create_user_access_token(user)

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }