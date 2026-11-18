"""Madea et al. (1994) — Hx, patent draft equation (10)."""
from app.services.pmi.biochemical_formula import (
    BiochemicalFormula, MeasurementRequirement, validate_estimate, validate_number,
)


def estimate_madea_h_1994_hours(concentration_mmol_l: float) -> float:
    value = validate_number(concentration_mmol_l, "hypoxanthine", nonnegative=True)
    return validate_estimate(3.69 * value + 1.29)


class MadeaH1994PMICalculator(BiochemicalFormula):
    def __init__(self):
        super().__init__(
            identifier="madea_h_1994",
            title="Madea et al. (1994) — Hx",
            equation=lambda values: estimate_madea_h_1994_hours(values["hypoxanthine"]),
            measurements=(MeasurementRequirement("hypoxanthine", "mmol_l", ("hplc",)),),
            sampling_window=None,
            areas=("europe", "north_europe", "scandinavia", "west_europe",),
            exclusions=("hyperthermia", "hypothermia", "chronic_pathologies", "electrolyte_disturbances",),
        )
