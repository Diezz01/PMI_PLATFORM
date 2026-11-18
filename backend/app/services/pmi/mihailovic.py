"""Mihailovic et al. (2012), patent draft equation (17)."""
from app.services.pmi.biochemical_formula import (
    BiochemicalFormula, MeasurementRequirement, validate_estimate, validate_number,
)


def estimate_mihailovic_hours(concentration_mmol_l: float) -> float:
    value = validate_number(concentration_mmol_l, "potassium", nonnegative=True)
    return validate_estimate(2.749 * value - 11.98)


class MihailovicPMICalculator(BiochemicalFormula):
    def __init__(self):
        super().__init__(
            identifier="mihailovic_2012",
            title="Mihailovic et al. (2012)",
            equation=lambda values: estimate_mihailovic_hours(values["potassium"]),
            measurements=(MeasurementRequirement("potassium", "mmol_l", ("potentiometer",)),),
            sampling_window=(3, 30),
            areas=("europe", "north_europe", "scandinavia", "west_europe",),
            exclusions=("sepsis", "intoxication", "kidney_disease", "chronic_pathologies", "high_blood_ammonium",),
        )
