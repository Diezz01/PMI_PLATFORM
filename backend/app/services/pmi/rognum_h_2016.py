"""Rognum et al. (2016), hypoxanthine variant, patent draft equation (23).

The interaction term is -0.05 * Hx * Ta as printed in the patent draft.
"""
from app.services.pmi.biochemical_formula import BiochemicalFormula, MeasurementRequirement


class RognumH2016PMICalculator(BiochemicalFormula):
    def __init__(self):
        super().__init__(
            identifier="rognum_h_2016", title="Rognum et al. (2016) — Hx",
            equation=lambda v: (0.215 * v["hypoxanthine"] - 0.467 * v["ambient_temperature_c"]
                                - 0.05 * v["hypoxanthine"] * v["ambient_temperature_c"] + 10.35),
            measurements=(MeasurementRequirement("hypoxanthine", "mmol_l", ("hplc",)),),
            required_values=("ambient_temperature_c",),
            sampling_window=(0.0, 60.0), areas=("north_europe", "scandinavia"),
            exclusions=("vitreous_contamination", "eye_trauma_or_disease"),
        )
