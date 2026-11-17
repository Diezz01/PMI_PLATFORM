"""Agrarwal et al. (1983), patent draft equation (4)."""
from app.services.pmi.potassium_formula import (
    PotassiumFormula,
    validate_estimate,
    validate_potassium,
)


def estimate_agrarwal_hours(potassium_mmol_l: float) -> float:
    return validate_estimate(1.94 * validate_potassium(potassium_mmol_l) - 7.65)


class AgrarwalPMICalculator(PotassiumFormula):
    def __init__(self):
        super().__init__(
            identifier="agrarwal_1983",
            title="Agrarwal et al. (1983)",
            equation=estimate_agrarwal_hours,
            sampling_window=(0.0, 35.0),
            techniques=("spectrophotometry",),
            areas=("india",),
            exclusions=(
                "vitreous_contamination",
                "hydration_changes",
                "electrolyte_disturbances",
            ),
        )
