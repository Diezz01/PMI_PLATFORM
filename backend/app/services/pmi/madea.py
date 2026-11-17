"""Madea et al. (1989), patent draft equation (6)."""
from app.services.pmi.biochemical_formula import (
    BiochemicalFormula, MeasurementRequirement, validate_estimate, validate_number,
)


def estimate_madea_hours(potassium_mmol_l: float) -> float:
    return validate_estimate(5.26 * validate_number(potassium_mmol_l, "Potassium", nonnegative=True) - 30.9)


class MadeaPMICalculator(BiochemicalFormula):
    def __init__(self):
        super().__init__(
            identifier="madea_1989",
            title="Madea et al. (1989)",
            equation=lambda values: estimate_madea_hours(values["potassium"]),
            sampling_window=(10.0, 120.0),
            measurements=(MeasurementRequirement("potassium", "mmol_l", ("potentiometer",)),),
            areas=("europe", "north_europe", "scandinavia", "west_europe"),
            exclusions=("kidney_disease", "agonal_period_over_6h", "high_blood_ammonium"),
        )
