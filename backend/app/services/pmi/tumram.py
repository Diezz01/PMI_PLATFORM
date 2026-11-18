"""Tumram et al. (2014), patent draft equation (20)."""
from app.services.pmi.biochemical_formula import (
    BiochemicalFormula, MeasurementRequirement, validate_estimate, validate_number,
)


def estimate_tumram_hours(concentration_mmol_l: float) -> float:
    value = validate_number(concentration_mmol_l, "potassium", nonnegative=True)
    return validate_estimate(2.71 * value - 20.19)


class TumramPMICalculator(BiochemicalFormula):
    def __init__(self):
        super().__init__(
            identifier="tumram_2014",
            title="Tumram et al. (2014)",
            equation=lambda values: estimate_tumram_hours(values["potassium"]),
            measurements=(MeasurementRequirement("potassium", "mmol_l", ("potentiometer",)),),
            sampling_window=(1.45, 35.18),
            areas=("india",),
            exclusions=("vitreous_contamination",),
        )
