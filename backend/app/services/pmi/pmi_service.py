from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.pmi_corrective_factor import PMICorrectiveFactor
from app.services.pmi.orchestrator import PMIOrchestrator


class InvalidCorrectionFactor(ValueError):
    """The supplied factor does not exist in the database catalog."""


class PMIService:

    def __init__(self):
        self.orchestrator = PMIOrchestrator()

    def list_correction_factors(self, *, db: Session) -> list[PMICorrectiveFactor]:
        statement = select(PMICorrectiveFactor).order_by(
            PMICorrectiveFactor.cf_value,
            PMICorrectiveFactor.id,
        )
        return list(db.scalars(statement).all())

    def calculate_all_methods(self, input_params: dict[str, Any], *, db: Session) -> list[dict[str, Any]]:
        factor_exists = select(
            select(PMICorrectiveFactor.id)
            .where(PMICorrectiveFactor.cf_value == input_params["correction_factor"])
            .exists()
        )
        if not db.scalar(factor_exists):
            raise InvalidCorrectionFactor("CF is not present in the database catalog")

        return self.orchestrator.calculate(input_params)

    def calculate_median(self, results: list[dict[str, Any]], selected_methods: list[str] )-> float:

        selected_results = [res for res in results if res["method_name"] in selected_methods]

        if not selected_results:
            raise ValueError("No Valid PMI result were selected")

        return self.orchestrator.calculate_median(selected_results)
