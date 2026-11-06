"""Add revoked authentication tokens."""

from alembic import op
import sqlalchemy as sa


revision = "8d0f64a95c21"
down_revision = "29e2440b73c1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "auth_revoked_tokens",
        sa.Column("jti", sa.String(length=32), nullable=False),
        sa.Column("expires_at", sa.BigInteger(), nullable=False),
        sa.PrimaryKeyConstraint("jti"),
    )

    op.create_index(
        "ix_auth_revoked_tokens_expires_at",
        "auth_revoked_tokens",
        ["expires_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_auth_revoked_tokens_expires_at",
        table_name="auth_revoked_tokens",
    )

    op.drop_table("auth_revoked_tokens")