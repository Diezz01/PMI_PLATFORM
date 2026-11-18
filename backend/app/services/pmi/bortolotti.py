"""Bortolotti et al. (2011), patent draft equation (15)."""
from app.services.pmi.biochemical_formula import (
    BiochemicalFormula, MeasurementRequirement, validate_estimate, validate_number,
)


def estimate_bortolotti_hours(concentration_mmol_l: float) -> float:
    value = validate_number(concentration_mmol_l, "potassium", nonnegative=True)
    return validate_estimate(5.77 * value - 13.28)


class BortolottiPMICalculator(BiochemicalFormula):
    def __init__(self):
        super().__init__(
            identifier="bortolotti_2011",
            title="Bortolotti et al. (2011)",
            equation=lambda values: estimate_bortolotti_hours(values["potassium"]),
            measurements=(MeasurementRequirement("potassium", "mmol_l", ("electrophoresis",)),),
            sampling_window=(1.8, 109),
            areas=("west_europe",),
            exclusions=("child", "vitreous_contamination", "chronic_pathologies", "eye_trauma_or_disease", "kidney_disease", "hyperthermia", "hypothermia", "drowning", "high_blood_ammonium",),
        )
