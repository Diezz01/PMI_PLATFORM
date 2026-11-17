"""Coe (1969), patent draft equation (2).

Branch validity is evaluated after adding the explicitly supplied time gap.
"""
from app.services.pmi.potassium_formula import (
    PotassiumFormula, validate_estimate, validate_potassium,
)
from app.schemas.pmi_results import PMICheckResult


def estimate_coe_hours(potassium_mmol_l: float, time_gap_minutes: int = 0) -> float:
    potassium = validate_potassium(potassium_mmol_l)
    early = 3.01 * potassium - 15.03
    late = 6.15 * potassium - 38.1
    return validate_estimate(early if early + time_gap_minutes / 60.0 < 6 else late)


class CoePMICalculator(PotassiumFormula):
    version = "development-2"
    required_parameters = ["potassium", "time_gap_minutes"]

    def __init__(self):
        super().__init__("coe_1969", "Coe (1969)", estimate_coe_hours, (0.5, 100.0))

    def estimate_hours(self, potassium, parameters):
        return estimate_coe_hours(potassium, parameters["time_gap_minutes"])

    def evaluate(self, parameters):
        gap = parameters.get("time_gap_minutes")
        if gap is None:
            return self._failure("missing_input", "required:time_gap_minutes",
                                 "Coe requires an explicit time gap to check its branch condition.")
        if isinstance(gap, bool) or not isinstance(gap, int) or gap < 0:
            return self._failure("invalid_input", "time_gap_adjustment", "Invalid time gap.")
        result = super().evaluate(parameters)
        if result.calculation_status == "calculated":
            early = 3.01 * parameters["potassium"]["value"] - 15.03
            early_branch = early + gap / 60.0 < 6
            adjusted = result.pmi_hours + gap / 60.0
            valid = 0 <= adjusted < 6 if early_branch else adjusted >= 6
            result.checks.append(PMICheckResult(
                id="coe_branch", outcome="passed" if valid else "failed",
                message="Coe branch condition after adding time gap: "
                        + ("PMI < 6 hours." if early_branch else "PMI >= 6 hours."),
            ))
        return result
