"""Stephens and Richards (1987), patent draft equation (5)."""
from app.services.pmi.biochemical_formula import (
    BiochemicalFormula, MeasurementRequirement, validate_estimate, validate_number,
)


def estimate_stephens_hours(potassium_mmol_l: float) -> float:
    return validate_estimate(4.20 * validate_number(potassium_mmol_l, "Potassium", nonnegative=True) - 26.65)


class StephensPMICalculator(BiochemicalFormula):
    def __init__(self):
        super().__init__(
            identifier="stephens_1987",
            title="Stephens and Richards (1987)",
            equation=lambda values: estimate_stephens_hours(values["potassium"]),
            sampling_window=(2.0, 35.0),
            measurements=(MeasurementRequirement("potassium", "mmol_l", ("potentiometer",)),),
            areas=("north_america", "usa"),
            exclusions=(
                "child", "vitreous_contamination", "sepsis", "intoxication",
                "hyperthermia", "hypothermia", "drowning", "electrolyte_disturbances",
            ),
        )
