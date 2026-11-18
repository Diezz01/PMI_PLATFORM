"""Salam et al. (2012), patent draft equation (16)."""
from app.services.pmi.biochemical_formula import (
    BiochemicalFormula, MeasurementRequirement, validate_estimate, validate_number,
)


def estimate_salam_hours(concentration_mmol_l: float) -> float:
    value = validate_number(concentration_mmol_l, "potassium", nonnegative=True)
    return validate_estimate(1.337 * value - 9.050)


class SalamPMICalculator(BiochemicalFormula):
    def __init__(self):
        super().__init__(
            identifier="salam_2012",
            title="Salam et al. (2012)",
            equation=lambda values: estimate_salam_hours(values["potassium"]),
            measurements=(MeasurementRequirement("potassium", "mmol_l", ("turbidimetric",)),),
            sampling_window=(8, 60),
            areas=("north_africa",),
            exclusions=("chronic_pathologies", "eye_trauma_or_disease", "kidney_disease", "head_trauma", "cerebral_hemorrhage", "high_blood_ammonium",),
        )
