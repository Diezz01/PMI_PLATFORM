"""Rognum et al. (2016), potassium variant, patent draft equation (23)."""
from app.services.pmi.biochemical_formula import BiochemicalFormula, MeasurementRequirement


class RognumK2016PMICalculator(BiochemicalFormula):
    def __init__(self):
        super().__init__(
            identifier="rognum_k_2016", title="Rognum et al. (2016) — K+",
            equation=lambda v: (5.184 * v["potassium"] - 0.174 * v["ambient_temperature_c"]
                                - 0.1 * v["potassium"] * v["ambient_temperature_c"] - 19.58),
            measurements=(MeasurementRequirement("potassium", "mmol_l", ("spectrophotometry",)),),
            required_values=("ambient_temperature_c",),
            sampling_window=(0.0, 60.0), areas=("north_europe", "scandinavia"),
            exclusions=("vitreous_contamination", "eye_trauma_or_disease"),
        )
