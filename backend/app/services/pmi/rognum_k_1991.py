"""Stephens and Richards (1987), patent draft equation (5)."""
from app.services.pmi.biochemical_formula import (
    BiochemicalFormula, MeasurementRequirement, validate_estimate, validate_number,
)

#PMI = 5.164∙[K^+ ]- 0.174∙Ta - 0.1∙[K^+ ]∙Ta- 19.58
def estimate_rognum_k_hours(potassium_mmol_l: float,ambient_temperature_c: float) -> float:
    k = validate_number(potassium_mmol_l, "Potassium", nonnegative=True
    )
    ta = validate_number( ambient_temperature_c, "Ambient temperature")

    return validate_estimate(
        5.164 * k
        - 0.174 * ta
        - 0.1 * k * ta
        - 19.58
    )


class RognumK1991PMICalculator(BiochemicalFormula):
    def __init__(self):
        super().__init__(
            identifier="stephens_1987",
            title="Stephens and Richards (1987)",
            equation=lambda values: estimate_rognum_k_hours(values["potassium"],values["ambient_temperature_c"],),
            sampling_window=(2.0, 35.0),
            measurements=(MeasurementRequirement("potassium", "mmol_l", ("potentiometer",)),),
            areas=("north_america", "usa"),
            exclusions=(
                "child", "vitreous_contamination", "sepsis", "intoxication",
                "hyperthermia", "hypothermia", "drowning", "electrolyte_disturbances",
            ),
            required_values=("ambient_temperature_c",),
        )
