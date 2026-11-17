"""Stephens and Richards (1987), patent draft equation (5)."""
from app.services.pmi.potassium_formula import (
    PotassiumFormula, validate_estimate, validate_potassium,
)


def estimate_stephens_hours(potassium_mmol_l: float) -> float:
    return validate_estimate(4.20 * validate_potassium(potassium_mmol_l) - 26.65)


class StephensPMICalculator(PotassiumFormula):
    def __init__(self):
        super().__init__(
            identifier="stephens_1987",
            title="Stephens and Richards (1987)",
            equation=estimate_stephens_hours,
            sampling_window=(2.0, 35.0),
            techniques=("potentiometer",),
            areas=("north_america", "usa"),
            exclusions=(
                "child", "vitreous_contamination", "sepsis", "intoxication",
                "hyperthermia", "hypothermia", "drowning", "electrolyte_disturbances",
            ),
        )
