"""Swain et al. (2015), patent draft equation (22)."""
from app.services.pmi.biochemical_formula import BiochemicalFormula, MeasurementRequirement


class SwainPMICalculator(BiochemicalFormula):
    def __init__(self):
        super().__init__(
            identifier="swain_2015", title="Swain et al. (2015)",
            equation=lambda v: 2.88 * v["potassium"] - 11.86,
            measurements=(MeasurementRequirement("potassium", "mmol_l", ("potentiometer",)),),
            sampling_window=(0.0, 96.0), areas=("india",),
            exclusions=("sepsis", "eye_trauma_or_disease", "head_trauma",
                        "cerebral_hemorrhage", "chronic_pathologies"),
        )
