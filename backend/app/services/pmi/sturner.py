"""Sturner (1963), patent draft equation (1)."""
from app.services.pmi.potassium_formula import (
    FormulaDomainError as SturnerDomainError,
    PotassiumInputError as SturnerInputError,
    PotassiumFormula,
    validate_estimate,
    validate_potassium,
)


def estimate_sturner_hours(potassium_mmol_l: float) -> float:
    return validate_estimate(7.14 * validate_potassium(potassium_mmol_l) - 39.1)


class SturnerPMICalculator(PotassiumFormula):
    def __init__(self):
        super().__init__(
            "sturner_1963", "Sturner et al. (1963)", estimate_sturner_hours,
            (0.0, 104.0), exclusions=("vitreous_contamination",),
        )
