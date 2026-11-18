"""James et al. (1997) — K+, patent draft equation (11)."""
from app.services.pmi.biochemical_formula import (
    BiochemicalFormula, MeasurementRequirement, validate_estimate, validate_number,
)


def estimate_james_k_1997_hours(concentration_mmol_l: float) -> float:
    value = validate_number(concentration_mmol_l, "potassium", nonnegative=True)
    return validate_estimate(4.32 * value - 18.35)


class JamesK1997PMICalculator(BiochemicalFormula):
    def __init__(self):
        super().__init__(
            identifier="james_k_1997",
            title="James et al. (1997) — K+",
            equation=lambda values: estimate_james_k_1997_hours(values["potassium"]),
            measurements=(MeasurementRequirement("potassium", "mmol_l", ("potentiometer",)),),
            sampling_window=(10, 80),
            areas=("usa",),
            exclusions=(),
        )
