"""James et al. (1997) — Hx, patent draft equation (11)."""
from app.services.pmi.biochemical_formula import (
    BiochemicalFormula, MeasurementRequirement, validate_estimate, validate_number,
)


def estimate_james_h_1997_hours(concentration_mmol_l: float) -> float:
    value = validate_number(concentration_mmol_l, "hypoxanthine", nonnegative=True)
    return validate_estimate(0.31 * value + 0.05)


class JamesH1997PMICalculator(BiochemicalFormula):
    def __init__(self):
        super().__init__(
            identifier="james_h_1997",
            title="James et al. (1997) — Hx",
            equation=lambda values: estimate_james_h_1997_hours(values["hypoxanthine"]),
            measurements=(MeasurementRequirement("hypoxanthine", "mmol_l", ("hplc",)),),
            sampling_window=(10, 80),
            areas=("usa",),
            exclusions=(),
        )
