"""Saldaña et al. (2019), patent draft equation (25).

K+ and Hx are in mmol/L; U/Am must explicitly contain urea in mg/dL.
"""
from app.services.pmi.biochemical_formula import BiochemicalFormula, MeasurementRequirement


class SaldanaPMICalculator(BiochemicalFormula):
    def __init__(self):
        super().__init__(
            identifier="saldana_2019", title="Saldaña et al. (2019)",
            equation=lambda v: 0.183 * v["hypoxanthine"] + 0.133 * v["u_am"] + 2.87 * v["potassium"],
            measurements=(
                MeasurementRequirement("potassium", "mmol_l", ("potentiometer",)),
                MeasurementRequirement("hypoxanthine", "mmol_l", ("hplc",)),
                MeasurementRequirement("u_am", "mg_dl", ("kinetic",), analyte="urea"),
            ),
            sampling_window=(0.0, 33.0), areas=("south_america",),
            exclusions=("eye_trauma_or_disease",),
        )
