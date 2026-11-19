"""Focardi et al. (2020), patent draft equation (27).

Albumin is in g/L. Its technique is not collected by the current input
contract, so the patent's nephelometry requirement remains unverified.
"""
from app.schemas.pmi_results import PMICheckResult
from app.services.pmi.biochemical_formula import BiochemicalFormula, MeasurementRequirement


class FocardiPMICalculator(BiochemicalFormula):
    def __init__(self):
        super().__init__(
            identifier="focardi_2020", title="Focardi et al. (2020)",
            equation=lambda v: 5.35 * v["potassium"] + 9.94 * v["albumin"] - 27.93,
            measurements=(
                MeasurementRequirement("potassium", "mmol_l", ("potentiometer",)),
                MeasurementRequirement("albumin", "g_l"),
            ),
            sampling_window=(0.0, 200.0), areas=("west_europe",),
            exclusions=("intoxication", "kidney_disease", "head_trauma", "cerebral_hemorrhage",
                        "chronic_pathologies", "electrolyte_disturbances"),
        )

    def evaluate(self, parameters):
        result = super().evaluate(parameters)
        if result.calculation_status == "calculated":
            result.checks.append(PMICheckResult(
                id="analytical_technique:albumin", field="albumin", outcome="unknown",
                message="Albumin nephelometry is required by the patent but its technique is not collected.",
            ))
        return result
