"""Madea et al. (1994) — K+, patent draft equation (10)."""
from app.services.pmi.biochemical_formula import (
    BiochemicalFormula, MeasurementRequirement, validate_estimate, validate_number,
)


def estimate_madea_k_1994_hours(concentration_mmol_l: float) -> float:
    value = validate_number(concentration_mmol_l, "potassium", nonnegative=True)
    return validate_estimate(6.31 * value + 0.179)


class MadeaK1994PMICalculator(BiochemicalFormula):
    def __init__(self):
        super().__init__(
            identifier="madea_k_1994",
            title="Madea et al. (1994) — K+",
            equation=lambda values: estimate_madea_k_1994_hours(values["potassium"]),
            measurements=(MeasurementRequirement("potassium", "mmol_l", ("potentiometer",)),),
            sampling_window=None,
            areas=("europe", "north_europe", "scandinavia", "west_europe",),
            exclusions=("hyperthermia", "hypothermia", "chronic_pathologies", "electrolyte_disturbances",),
        )
