"""Devenaux et al. (1985), patent draft equation (7)."""
from app.services.pmi.potassium_formula import (
    PotassiumFormula, validate_estimate, validate_potassium,
)


def estimate_devenaux_hours(potassium_mmol_l: float) -> float:
    return validate_estimate((validate_potassium(potassium_mmol_l) - 7.60) / 0.124)


class DevenauxPMICalculator(PotassiumFormula):
    def __init__(self):
        super().__init__(
            identifier="devenaux_1985",
            title="Devenaux et al. (1985)",
            equation=estimate_devenaux_hours,
            sampling_window=(0.0, 168.0),
            techniques=("spectrophotometry",),
            areas=("europe", "north_europe", "scandinavia", "west_europe"),
            exclusions=("vitreous_contamination",),
        )
