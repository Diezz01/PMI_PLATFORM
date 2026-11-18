"""Gamero et al. (1992), patent draft equation (9)."""
from app.services.pmi.biochemical_formula import (
    BiochemicalFormula, MeasurementRequirement, validate_estimate, validate_number,
)


def estimate_gamero_hours(concentration_mmol_l: float) -> float:
    value = validate_number(concentration_mmol_l, "potassium", nonnegative=True)
    return validate_estimate((value - 6.347) / 0.158)


class GameroPMICalculator(BiochemicalFormula):
    def __init__(self):
        super().__init__(
            identifier="gamero_1992",
            title="Gamero et al. (1992)",
            equation=lambda values: estimate_gamero_hours(values["potassium"]),
            measurements=(MeasurementRequirement("potassium", "mmol_l", ("spectrophotometry",)),),
            sampling_window=(0, 24),
            areas=("west_europe",),
            exclusions=(),
        )
