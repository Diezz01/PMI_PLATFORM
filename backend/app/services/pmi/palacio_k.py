"""Palacio et al. (2020), potassium variant, patent draft equation (26)."""
import math

from app.services.pmi.biochemical_formula import (
    BiochemicalFormula, FormulaDomainError, MeasurementRequirement, validate_number,
)


def estimate_palacio_k_hours(potassium_mmol_l: float) -> float:
    potassium = validate_number(potassium_mmol_l, "Potassium", nonnegative=True)
    # K = -0.0005*t² + 0.2018*t + 6.173. The vertex is at 201.8 h;
    # the decreasing branch is entirely outside the stated 0-186 h window.
    if potassium > 26.53462:
        raise FormulaDomainError("Palacio requires K+ <= 26.53462 mmol/L for real roots.")
    discriminant = 0.2018 ** 2 - 4 * 0.0005 * (potassium - 6.173)
    if discriminant < 0:
        raise FormulaDomainError("Palacio's potassium equation has no real root.")
    # Rationalized smaller root avoids cancellation near K=6.173.
    hours = 2 * (potassium - 6.173) / (0.2018 + math.sqrt(discriminant))
    if not 0 <= hours <= 186:
        raise FormulaDomainError("No potassium root lies within Palacio's 0-186 hour window.")
    return hours


class PalacioKPMICalculator(BiochemicalFormula):
    def __init__(self):
        super().__init__(
            identifier="palacio_k_2020", title="Palacio et al. (2020) — K+",
            equation=lambda v: estimate_palacio_k_hours(v["potassium"]),
            measurements=(MeasurementRequirement("potassium", "mmol_l", ("electrophoresis",)),),
            sampling_window=(0.0, 186.0), areas=("west_europe",),
            exclusions=("intoxication", "head_trauma", "cerebral_hemorrhage"),
        )
