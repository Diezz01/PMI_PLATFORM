"""Madea et al. (1989), patent draft equation (6)."""
from app.services.pmi.potassium_formula import (
    PotassiumFormula, validate_estimate, validate_potassium,
)


def estimate_madea_hours(potassium_mmol_l: float) -> float:
    return validate_estimate(5.26 * validate_potassium(potassium_mmol_l) - 30.9)


class MadeaPMICalculator(PotassiumFormula):
    def __init__(self):
        super().__init__(
            identifier="madea_1989",
            title="Madea et al. (1989)",
            equation=estimate_madea_hours,
            sampling_window=(10.0, 120.0),
            techniques=("potentiometer",),
            areas=("europe", "north_europe", "scandinavia", "west_europe"),
            exclusions=("kidney_disease", "agonal_period_over_6h", "high_blood_ammonium"),
        )
