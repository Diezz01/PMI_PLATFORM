from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class RevokedToken(Base):
    __tablename__ = "auth_revoked_tokens"

    jti: Mapped[str] = mapped_column(
        String(32),
        primary_key=True,
    )

    expires_at: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        index=True,
    )