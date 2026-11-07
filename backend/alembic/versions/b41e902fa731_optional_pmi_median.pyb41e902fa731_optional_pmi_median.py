"""Allow saving PMI results without a median."""

from alembic import op
import sqlalchemy as sa


revision = "b41e902fa731"
down_revision = "8d0f64a95c21"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "pmi_calculations",
        "median_pmi",
        existing_type=sa.Float(),
        nullable=True,
    )
    op.add_column(
        "pmi_calculations",
        sa.Column("evaluation_snapshot", sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    connection = op.get_bind()
    has_null_medians = connection.execute(
        sa.text(
            "SELECT EXISTS ("
            "SELECT 1 FROM pmi_calculations WHERE median_pmi IS NULL"
            ")"
        )
    ).scalar_one()

    if has_null_medians:
        raise RuntimeError(
            "Cannot restore mandatory median: saved calculations "
            "without a median exist."
        )

    op.drop_column("pmi_calculations", "evaluation_snapshot")
    op.alter_column(
        "pmi_calculations",
        "median_pmi",
        existing_type=sa.Float(),
        nullable=False,
    )