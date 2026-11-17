"""Devenaux et al. (1985), patent draft equation (7)."""
from app.services.pmi.biochemical_formula import (
    BiochemicalFormula, MeasurementRequirement, validate_estimate, validate_number,
)


def estimate_devenaux_hours(potassium_mmol_l: float) -> float:
    return validate_estimate((validate_number(potassium_mmol_l, "Potassium", nonnegative=True) - 7.60) / 0.124)


class DevenauxPMICalculator(BiochemicalFormula):
    def __init__(self):
        super().__init__(
            identifier="devenaux_1985",
            title="Devenaux et al. (1985)",
            equation=lambda values: estimate_devenaux_hours(values["potassium"]),
            sampling_window=(0.0, 168.0),
            measurements=(MeasurementRequirement("potassium", "mmol_l", ("spectrophotometry",)),),
            areas=("europe", "north_europe", "scandinavia", "west_europe"),
            exclusions=("vitreous_contamination",),
        )
