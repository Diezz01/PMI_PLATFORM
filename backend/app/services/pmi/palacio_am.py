"""Palacio et al. (2020), ammonium variant, patent draft equation (26)."""
import math

from app.services.pmi.biochemical_formula import (
    BiochemicalFormula, FormulaDomainError, MeasurementRequirement, validate_number,
)


def estimate_palacio_am_hours(ammonium_mmol_l: float) -> float:
    ammonium = validate_number(ammonium_mmol_l, "Ammonium", nonnegative=True)
    if ammonium < 0.1461:
        raise FormulaDomainError("Palacio requires ammonium >= 0.1461 mmol/L for a non-negative PMI.")
    # NH4+ = 2e-6*t² + 0.0127*t + 0.1461; the other root is negative.
    difference = ammonium - 0.1461
    hours = 2 * difference / (0.0127 + math.sqrt(0.0127 ** 2 + 8e-6 * difference))
    if not 0 <= hours <= 186:
        raise FormulaDomainError("No ammonium root lies within Palacio's 0-186 hour window.")
    return hours


class PalacioAmPMICalculator(BiochemicalFormula):
    def __init__(self):
        super().__init__(
            identifier="palacio_am_2020", title="Palacio et al. (2020) — NH4+",
            equation=lambda v: estimate_palacio_am_hours(v["u_am"]),
            measurements=(MeasurementRequirement("u_am", "mmol_l", ("electrophoresis",), analyte="ammonium"),),
            sampling_window=(0.0, 186.0), areas=("west_europe",),
            exclusions=("intoxication", "head_trauma", "cerebral_hemorrhage"),
        )
