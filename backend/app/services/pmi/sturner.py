"""Numerical implementation of Sturner et al. (1963).

Input: vitreous potassium concentration in mmol/L.
Output: estimated PMI in hours, relative to sampling.
Applicability checks and time-gap adjustment are handled separately.
"""

import math

from typing import Any

from app.schemas.pmi_results import PMICheckResult, PMIMethodResult
from app.services.pmi.base_calculator import PMICalculator


class SturnerInputError(ValueError):
    """The potassium input is not a valid concentration."""


class SturnerDomainError(ValueError):
    """The equation does not produce an admissible PMI."""


def estimate_sturner_hours(potassium_mmol_l: float) -> float:

    """Return the raw estimate: 7.14 * potassium - 39.1."""

    if (
        isinstance(potassium_mmol_l, bool)
        or not isinstance(potassium_mmol_l, (int, float))
    ):
        raise SturnerInputError(
            "Potassium must be a number expressed in mmol/L."
        )

    if not math.isfinite(potassium_mmol_l):
        raise SturnerInputError(
            "Potassium must be finite."
        )

    if potassium_mmol_l < 0:
        raise SturnerInputError(
            "Potassium concentration cannot be negative."
        )

    pmi_hours = 7.14 * potassium_mmol_l - 39.1

    if not math.isfinite(pmi_hours):
        raise SturnerDomainError(
            "The equation produced a non-finite PMI."
        )

    if pmi_hours < 0:
        raise SturnerDomainError(
            "The equation produced a negative PMI."
        )

    return pmi_hours

class SturnerPMICalculator(PMICalculator):
    @property
    def name(self) -> str:
        return "sturner_1963"

    @property
    def version(self) -> str:
        return "development-1"

    @property
    def method_kind(self) -> str:
        return "biochemical"

    @property
    def required_parameters(self) -> list[str]:
        return ["potassium"]

    def _failure(
        self,
        status: str,
        check_id: str,
        message: str,
    ) -> PMIMethodResult:
        return PMIMethodResult(
            method_id=self.name,
            method_name="Sturner et al. (1963)",
            method_version=self.version,
            method_kind=self.method_kind,
            calculation_status=status,
            pmi_hours=None,
            time_reference=None,
            checks=[
                PMICheckResult(
                    id=check_id,
                    outcome="failed",
                    field="potassium",
                    message=message,
                )
            ],
        )

    def evaluate(
        self,
        parameters: dict[str, Any],
    ) -> PMIMethodResult:
        potassium = parameters.get("potassium")

        if potassium is None:
            return self._failure(
                "missing_input",
                "required:potassium",
                "Vitreous potassium has not been provided.",
            )

        if not isinstance(potassium, dict):
            return self._failure(
                "invalid_input",
                "potassium_structure",
                "Potassium must be a measurement object.",
            )

        if potassium.get("status") == "unavailable":
            return self._failure(
                "missing_input",
                "required:potassium",
                "Vitreous potassium is unavailable.",
            )

        if potassium.get("status") != "available":
            return self._failure(
                "invalid_input",
                "potassium_status",
                "The potassium availability status is invalid.",
            )

        if potassium.get("value") is None:
            return self._failure(
                "missing_input",
                "required:potassium.value",
                "The potassium concentration is missing.",
            )

        try:
            hours = estimate_sturner_hours(potassium["value"])
        except SturnerInputError as exc:
            return self._failure(
                "invalid_input", "potassium_value", str(exc)
            )
        except SturnerDomainError as exc:
            return self._failure(
                "invalid_domain", "pmi_domain", str(exc)
            )

        checks = [
            PMICheckResult(
                id="numerical_result",
                outcome="passed",
                field="potassium.value",
                message=(
                    "Calculated using PMI = 7.14 * K+ - 39.1, "
                    "with potassium expressed in mmol/L."
                ),
            )
        ]

        # "all" bypasses only the technique restriction.
        technique = potassium.get("technique") or {}
        mode = technique.get("mode")

        if mode == "all":
            technique_outcome = "skipped"
            technique_message = (
                "The user selected all techniques. "
                "The technique restriction was explicitly bypassed."
            )
        elif mode == "specific":
            compatible = technique.get("id") == "photometer"
            technique_outcome = "passed" if compatible else "failed"
            technique_message = (
                "The selected technique is photometry."
                if compatible
                else "This model requires photometry."
            )
        else:
            technique_outcome = "unknown"
            technique_message = (
                "The analytical technique has not been verified."
            )

        checks.append(
            PMICheckResult(
                id="analytical_technique",
                outcome=technique_outcome,
                field="potassium.technique",
                message=technique_message,
            )
        )

        # USA is a geographical subset of North America.
        area = parameters.get("subject_area")

        if area is None:
            area_outcome = "unknown"
            area_message = "The subject's geographical origin is missing."
        elif area in {"north_america", "usa"}:
            area_outcome = "passed"
            area_message = "The subject originates from North America."
        else:
            area_outcome = "failed"
            area_message = (
                "The reported geographical origin does not match "
                "the North American population specified for this model."
            )

        checks.append(
            PMICheckResult(
                id="geographical_origin",
                outcome=area_outcome,
                field="subject_area",
                message=area_message,
            )
        )

        criteria = parameters.get("exclusion_criteria") or {}
        contamination = criteria.get("vitreous_contamination")

        if contamination == "absent":
            contamination_outcome = "passed"
            contamination_message = (
                "Vitreous contamination was explicitly reported absent."
            )
        elif contamination == "present":
            contamination_outcome = "failed"
            contamination_message = (
                "Vitreous contamination was reported present; "
                "the model's applicability condition is not satisfied."
            )
        else:
            contamination_outcome = "unknown"
            contamination_message = (
                "The absence of vitreous contamination is not established."
            )

        checks.append(
            PMICheckResult(
                id="vitreous_contamination",
                outcome=contamination_outcome,
                field="exclusion_criteria.vitreous_contamination",
                message=contamination_message,
            )
        )

        checks.append(
            PMICheckResult(
                id="sampling_window",
                outcome="unknown",
                message=(
                    "The patent specifies sampling within 104 hours "
                    "after death. This condition has not been independently "
                    "verified. The calculated PMI alone does not establish it."
                ),
            )
        )

        return PMIMethodResult(
            method_id=self.name,
            method_name="Sturner et al. (1963)",
            method_version=self.version,
            method_kind=self.method_kind,
            calculation_status="calculated",
            pmi_hours=hours,
            time_reference="sampling",
            checks=checks,
        )