"""Muñoz et al. (2001), patent draft equation (12)."""
from app.services.pmi.biochemical_formula import (
    BiochemicalFormula, MeasurementRequirement, validate_estimate, validate_number,
)


def estimate_munoz_hours(concentration_mmol_l: float) -> float:
    value = validate_number(concentration_mmol_l, "potassium", nonnegative=True)
    return validate_estimate(3.92 * value - 19.04)


class MunozPMICalculator(BiochemicalFormula):
    def __init__(self):
        super().__init__(
            identifier="munoz_2001",
            title="Muñoz et al. (2001)",
            equation=lambda values: estimate_munoz_hours(values["potassium"]),
            measurements=(MeasurementRequirement("potassium", "mmol_l", ("potentiometer",)),),
            sampling_window=(1, 40.45),
            areas=("west_europe",),
            exclusions=("child", "vitreous_contamination",),
        )
