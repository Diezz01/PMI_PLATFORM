"""Jashnani et al. (2010), patent draft equation (14)."""
from app.services.pmi.biochemical_formula import (
    BiochemicalFormula, MeasurementRequirement, validate_estimate, validate_number,
)


def estimate_jashnani_hours(concentration_mmol_l: float) -> float:
    value = validate_number(concentration_mmol_l, "potassium", nonnegative=True)
    return validate_estimate(1.076 * value - 2.81)


class JashnaniPMICalculator(BiochemicalFormula):
    def __init__(self):
        super().__init__(
            identifier="jashnani_2010",
            title="Jashnani et al. (2010)",
            equation=lambda values: estimate_jashnani_hours(values["potassium"]),
            measurements=(MeasurementRequirement("potassium", "mmol_l", ("photometer",)),),
            sampling_window=(10, 50),
            areas=("india",),
            exclusions=("child",),
        )
