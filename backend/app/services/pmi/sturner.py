"""Sturner (1963), patent draft equation (1)."""
from app.services.pmi.potassium_formula import (
    PotassiumFormula,
    validate_estimate,
    validate_potassium,
)


def estimate_sturner_hours(potassium_mmol_l: float) -> float:
    return validate_estimate(7.14 * validate_potassium(potassium_mmol_l) - 39.1)


class SturnerPMICalculator(PotassiumFormula):
    def __init__(self):
        super().__init__(
            identifier="sturner_1963", title="Sturner et al. (1963)", equation=estimate_sturner_hours,
            sampling_window=(0.0, 104.0),techniques=("photometer"),areas=("usa", "north_america"), exclusions=("vitreous_contamination",),
        )
