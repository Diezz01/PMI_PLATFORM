"""Zhou et al. (2007), patent draft equation (13)."""
from app.services.pmi.biochemical_formula import (
    BiochemicalFormula, MeasurementRequirement, validate_estimate, validate_number,
)


def estimate_zhou_hours(concentration_mmol_l: float) -> float:
    value = validate_number(concentration_mmol_l, "potassium", nonnegative=True)
    return validate_estimate(5.88 * value - 32.71)


class ZhouPMICalculator(BiochemicalFormula):
    def __init__(self):
        super().__init__(
            identifier="zhou_2007",
            title="Zhou et al. (2007)",
            equation=lambda values: estimate_zhou_hours(values["potassium"]),
            measurements=(MeasurementRequirement("potassium", "mmol_l", ("chromatography",)),),
            sampling_window=(1, 27),
            areas=("china",),
            exclusions=("vitreous_contamination", "decomposition", "electrolyte_disturbances", "eye_trauma_or_disease",),
        )
