from typing import Callable

import jwt
from jwt.exceptions import InvalidTokenError
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import re

from app.models.revoked_token import RevokedToken
from app.configs.config import settings
from app.database import get_db
from app.models.user import User


AUTH_COOKIE_NAME = "pmi_access_token"

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login",
    auto_error=False,
)


def authentication_error() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


def require_web_origin(request: Request) -> None:
    if (
        request.headers.get("origin") != settings.FRONTEND_ORIGIN
        or request.headers.get("x-pmi-request") != "1"
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Request origin is not allowed",
        )


def decode_credentials(token: str) -> tuple[int, int, str]:
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            options={"require": ["sub", "exp", "jti"]},
        )

        subject = payload["sub"]
        expires_at = payload["exp"]
        jti = payload["jti"]

        if not isinstance(subject, str):
            raise ValueError("Invalid subject")

        user_id = int(subject)

        if user_id <= 0 or type(expires_at) is not int:
            raise ValueError("Invalid token claims")

        if (
            not isinstance(jti, str)
            or re.fullmatch(r"[0-9a-f]{32}", jti) is None
        ):
            raise ValueError("Invalid token identifier")

    except (InvalidTokenError, ValueError, TypeError, OverflowError):
        raise authentication_error() from None

    return user_id, expires_at, jti


def get_current_auth(
    request: Request,
    bearer_token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> tuple[User, int]:
    token = bearer_token

    if token is None:
        token = request.cookies.get(AUTH_COOKIE_NAME)

        if token and request.method not in {"GET", "HEAD", "OPTIONS"}:
            require_web_origin(request)

    if not token:
        raise authentication_error()

    user_id, expires_at, jti = decode_credentials(token)

    if db.get(RevokedToken, jti) is not None:
        raise authentication_error()

    user = db.get(User, user_id)

    if user is None:
        raise authentication_error()

    return user, expires_at


def get_current_user(
    auth: tuple[User, int] = Depends(get_current_auth),
) -> User:
    user, _ = auth
    return user


def require_role(required_role: str) -> Callable:
    def role_check(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if current_user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permission",
            )

        return current_user

    return role_check