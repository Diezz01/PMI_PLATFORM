from sqlalchemy import Float, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class PMICorrectiveFactor(Base):
    __tablename__ = "pmi_corrective_factors"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    cf_value: Mapped[float] = mapped_column(Float, nullable=False)

    dry_clothing_or_covering: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )

    in_air: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )

    wet_through_clothing_or_covering_or_wet_body_surface: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )

    water: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )
