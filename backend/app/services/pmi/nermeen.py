"""Nermeen et al. (2013), patent draft equation (18)."""
from app.services.pmi.biochemical_formula import (
    BiochemicalFormula, MeasurementRequirement, validate_estimate, validate_number,
)


def estimate_nermeen_hours(concentration_mmol_l: float) -> float:
    value = validate_number(concentration_mmol_l, "potassium", nonnegative=True)
    return validate_estimate(8.77 * value - 53.90)


class NermeenPMICalculator(BiochemicalFormula):
    def __init__(self):
        super().__init__(
            identifier="nermeen_2013",
            title="Nermeen et al. (2013)",
            equation=lambda values: estimate_nermeen_hours(values["potassium"]),
            measurements=(MeasurementRequirement("potassium", "mmol_l", ("spectrophotometry",)),),
            sampling_window=(0, 100),
            areas=("north_africa",),
            exclusions=("eye_trauma_or_disease", "kidney_disease", "hydration_changes", "high_blood_ammonium",),
        )
