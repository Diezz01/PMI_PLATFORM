"""create PMI corrective factors table

Revision ID: 29e2440b73c1
Revises: c70582cbc254
Create Date: 2026-10-13

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "29e2440b73c1"
down_revision: Union[str, Sequence[str], None] = "c70582cbc254"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "pmi_corrective_factors",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("cf_value", sa.Float(), nullable=False),
        sa.Column("dry_clothing_or_covering", sa.String(), nullable=True),
        sa.Column("in_air", sa.String(), nullable=True),
        sa.Column(
            "wet_through_clothing_or_covering_or_wet_body_surface",
            sa.String(),
            nullable=True,
        ),
        sa.Column("water", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("pmi_corrective_factors")
