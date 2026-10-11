from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, JSON, func,String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class PMICalculation(Base):
    __tablename__ = "pmi_calculations"

    id: Mapped[int] = mapped_column(primary_key = True, autoincrement=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    session_id: Mapped[str | None] = mapped_column(String(64),unique=True,nullable=True)

    input_data: Mapped[dict] = mapped_column(JSON, nullable=False)

    #contains the selected methods used to calculate the median
    #it is possible that a user wants to calculate the median by choosing the prefered available results instead of the total amount
    median_selected_methods: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list, server_default=text("'[]'"))

    median_pmi: Mapped[float] = mapped_column(Float, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),server_default=func.now(), nullable=False)

    results: Mapped[list["PMIResult"]] = relationship(back_populates="calculation", cascade="all, delete-orphan")


class PMIResult(Base):
    __tablename__ = "pmi_results"

    id: Mapped[int] = mapped_column(primary_key = True, autoincrement=True)

    calculation_id: Mapped[int] = mapped_column(ForeignKey("pmi_calculations.id"), nullable=False)

    method_name: Mapped[str] = mapped_column(nullable=False)

    pmi_value: Mapped[float] = mapped_column(Float, nullable=False)

    parameters: Mapped[dict] = mapped_column(JSON, nullable=False)

    method_version: Mapped[str] = mapped_column(nullable=False)

    calculation: Mapped["PMICalculation"] = relationship(back_populates="results")