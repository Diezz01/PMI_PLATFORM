"""Siddamsetty et al. (2013), patent draft equation (19)."""
from app.services.pmi.biochemical_formula import (
    BiochemicalFormula, MeasurementRequirement, validate_estimate, validate_number,
)


def estimate_siddamsetty_hours(concentration_mmol_l: float) -> float:
    value = validate_number(concentration_mmol_l, "potassium", nonnegative=True)
    return validate_estimate(4.701 * value - 29.06)


class SiddamsettyPMICalculator(BiochemicalFormula):
    def __init__(self):
        super().__init__(
            identifier="siddamsetty_2013",
            title="Siddamsetty et al. (2013)",
            equation=lambda values: estimate_siddamsetty_hours(values["potassium"]),
            measurements=(MeasurementRequirement("potassium", "mmol_l", ("potentiometer",)),),
            sampling_window=(0, 170),
            areas=("india",),
            exclusions=("eye_trauma_or_disease", "kidney_disease", "hydration_changes", "high_blood_ammonium", "electrolyte_disturbances", "vitreous_contamination",),
        )
