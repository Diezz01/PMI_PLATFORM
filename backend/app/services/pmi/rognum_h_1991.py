"""Rognum et al. (1991), hypoxanthine variant, patent draft equation (8)."""
from app.services.pmi.biochemical_formula import (
    BiochemicalFormula,
    MeasurementRequirement,
    validate_estimate,
    validate_number,
)


def estimate_rognum_h_hours(hypoxanthine_mmol_l: float,ambient_temperature_c: float,) -> float:
    hx = validate_number(hypoxanthine_mmol_l, "Hypoxanthine", nonnegative=True)
    ta = validate_number(ambient_temperature_c, "Ambient temperature")
    return validate_estimate(0.215 * hx - 0.467 * ta + 0.005 * hx * ta + 10.353)


class RognumH1991PMICalculator(BiochemicalFormula):
    def __init__(self):
        super().__init__(
            identifier="rognum_h_1991",
            title="Rognum et al. (1991) — Hx",
            equation=lambda values: estimate_rognum_h_hours(
                values["hypoxanthine"], values["ambient_temperature_c"],
            ),
            measurements=(MeasurementRequirement("hypoxanthine", "mmol_l", ("hplc",)),),
            required_values=("ambient_temperature_c",),
            sampling_window=(0.0, 120.0),
            areas=("north_europe", "scandinavia"),
            exclusions=("vitreous_contamination", "eye_trauma_or_disease"),
        )
