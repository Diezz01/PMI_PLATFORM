"""Adjutantis et al. (1972)"""
from app.services.pmi.biochemical_formula import (
    BiochemicalFormula, MeasurementRequirement,
    validate_estimate,
    validate_number,
)


def estimate_adjutantis_hours(potassium_mmol_l: float) -> float:
    return validate_estimate(1.36 * validate_number(potassium_mmol_l, "Potassium", nonnegative=True) - 2.93)


class AdjutantisPMICalculator(BiochemicalFormula):
    def __init__(self):
        super().__init__(
            identifier="adjutantis_1972", title="Adjutantis et al. (1972)", equation=lambda values: estimate_adjutantis_hours(values["potassium"]),
            sampling_window=(0.0, 12.0),areas=("europe","north_europe","west_europe"), exclusions=(),measurements=(MeasurementRequirement("potassium", "mmol_l", ("spectrophotometry",)),)
        )
