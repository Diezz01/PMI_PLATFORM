"""Agrarwal et al. (1983), patent draft equation (4)."""
from app.services.pmi.biochemical_formula import (
    BiochemicalFormula, MeasurementRequirement,
    validate_estimate,
    validate_number,
)


def estimate_agrarwal_hours(potassium_mmol_l: float) -> float:
    return validate_estimate(1.94 * validate_number(potassium_mmol_l, "Potassium", nonnegative=True) - 7.65)


class AgrarwalPMICalculator(BiochemicalFormula):
    def __init__(self):
        super().__init__(
            identifier="agrarwal_1983",
            title="Agrarwal et al. (1983)",
            equation=lambda values: estimate_agrarwal_hours(values["potassium"]),
            sampling_window=(0.0, 35.0),
            measurements=(MeasurementRequirement("potassium", "mmol_l", ("spectrophotometry",)),),
            areas=("india",),
            exclusions=(
                "vitreous_contamination",
                "hydration_changes",
                "electrolyte_disturbances",
            ),
        )
