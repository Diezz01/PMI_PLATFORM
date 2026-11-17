"""Sturner (1963), patent draft equation (1)."""
from app.services.pmi.biochemical_formula import (
    BiochemicalFormula, MeasurementRequirement,
    validate_estimate,
    validate_number,
)


def estimate_sturner_hours(potassium_mmol_l: float) -> float:
    return validate_estimate(7.14 * validate_number(potassium_mmol_l, "Potassium", nonnegative=True) - 39.1)


class SturnerPMICalculator(BiochemicalFormula):
    def __init__(self):
        super().__init__(
            identifier="sturner_1963", title="Sturner et al. (1963)", equation=lambda values: estimate_sturner_hours(values["potassium"]),
            sampling_window=(0.0, 104.0),measurements=(MeasurementRequirement("potassium", "mmol_l", ("photometer",)),),areas=("usa", "north_america"), exclusions=("vitreous_contamination",),
        )
