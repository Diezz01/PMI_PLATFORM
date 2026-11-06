import time

from fastapi import APIRouter, Depends, HTTPException, Response, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.revoked_token import RevokedToken
from app.configs.config import settings
from app.configs.dependencies import (
    AUTH_COOKIE_NAME,
    decode_credentials,
    get_current_auth,
    require_web_origin,
    oauth2_scheme
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
    _, expires_at, _ = decode_credentials(token)

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

@router.post(
    "/logout",
    status_code=204,
    response_class=Response,
    dependencies=[Depends(require_web_origin)],
)
def logout(
    request: Request,
    bearer_token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    token = bearer_token or request.cookies.get(AUTH_COOKIE_NAME)

    if token:
        try:
            _, expires_at, jti = decode_credentials(token)
        except HTTPException as error:
            if error.status_code != 401:
                raise
            # An invalid or expired token is already unusable.
        else:
            if db.get(RevokedToken, jti) is None:
                db.add(
                    RevokedToken(
                        jti=jti,
                        expires_at=expires_at,
                    )
                )

                try:
                    db.commit()
                except IntegrityError:
                    db.rollback()

                    # Another concurrent logout may have revoked it.
                    if db.get(RevokedToken, jti) is None:
                        raise

    response = Response(status_code=204)

    response.delete_cookie(
        key=AUTH_COOKIE_NAME,
        path="/",
        secure=settings.AUTH_COOKIE_SECURE,
        httponly=True,
        samesite="lax",
    )

    response.headers["Cache-Control"] = "no-store"

    return response