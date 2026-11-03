import time

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.configs.config import settings
from app.configs.dependencies import (
    AUTH_COOKIE_NAME,
    decode_credentials,
    get_current_auth,
    require_web_origin,
)
from app.database import get_db
from app.models.user import User
from app.schemas.user import AuthSessionResponse
from app.services.auth_service import auth_user, create_user_access_token


router = APIRouter(
    prefix="/auth",
    tags=["Web authentication"],
)


@router.post(
    "/session",
    response_model=AuthSessionResponse,
    dependencies=[Depends(require_web_origin)],
)
def create_web_session(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = auth_user(db, form_data.username, form_data.password)

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password",
        )

    token = create_user_access_token(user)
    _, expires_at = decode_credentials(token)

    response.set_cookie(
        key=AUTH_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=settings.AUTH_COOKIE_SECURE,
        samesite="lax",
        path="/",
        max_age=max(0, expires_at - int(time.time())),
    )
    response.headers["Cache-Control"] = "no-store"

    return {
        "user": user,
        "expires_at": expires_at,
    }


@router.get(
    "/session",
    response_model=AuthSessionResponse,
)
def read_web_session(
    response: Response,
    auth: tuple[User, int] = Depends(get_current_auth),
):
    user, expires_at = auth

    response.headers["Cache-Control"] = "no-store"

    return {
        "user": user,
        "expires_at": expires_at,
    }