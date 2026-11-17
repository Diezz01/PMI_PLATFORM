"""Adjutantis et al. (1972)"""
from app.services.pmi.potassium_formula import (
    PotassiumFormula,
    validate_estimate,
    validate_potassium,
)


def estimate_adjutantis_hours(potassium_mmol_l: float) -> float:
    return validate_estimate(1.36 * validate_potassium(potassium_mmol_l) - 2.93)


class AdjutantisPMICalculator(PotassiumFormula):
    def __init__(self):
        super().__init__(
            identifier="adjutantis_1972", title="Adjutantis et al. (1972)", equation=estimate_adjutantis_hours,
            sampling_window=(0.0, 12.0),areas=("europe","north_europe","west_europe"), exclusions=(""),techniques=("spectrophotometry")
        )
