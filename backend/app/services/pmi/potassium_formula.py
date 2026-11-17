"""Shared validation and applicability checks for potassium-only formulas."""
import math
from collections.abc import Callable
from typing import Any

from app.schemas.pmi_results import PMICheckResult, PMIMethodResult
from app.services.pmi.base_calculator import PMICalculator


class PotassiumInputError(ValueError):
    pass


class FormulaDomainError(ValueError):
    pass


def validate_potassium(value: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise PotassiumInputError("Potassium must be a number in mmol/L.")
    if not math.isfinite(value) or value < 0:
        raise PotassiumInputError("Potassium must be finite and non-negative.")
    return value


def validate_estimate(hours: float) -> float:
    if not math.isfinite(hours) or hours < 0:
        raise FormulaDomainError("The equation produced a negative or non-finite PMI.")
    return hours


class PotassiumFormula(PMICalculator):
    version = "development-2"
    method_kind = "biochemical"
    required_parameters = ["potassium"]

    def __init__(
        self, identifier: str, title: str, equation: Callable[[float], float],
        sampling_window: tuple[float, float], *,
        techniques: tuple[str, ...] = ("photometer",),
        areas: tuple[str, ...] = ("north_america", "usa"),
        exclusions: tuple[str, ...] = (),
    ):
        self.identifier, self.title, self.equation = identifier, title, equation
        self.sampling_window = sampling_window
        self.techniques, self.areas, self.exclusions = techniques, areas, exclusions

    @property
    def name(self) -> str:
        return self.identifier

    def _result(self, status, checks, hours=None):
        return PMIMethodResult(
            method_id=self.name, method_name=self.title, method_version=self.version,
            method_kind=self.method_kind, calculation_status=status, pmi_hours=hours,
            time_reference="sampling" if hours is not None else None, checks=checks,
        )

    def _failure(self, status, check_id, message):
        return self._result(status, [PMICheckResult(
            id=check_id, outcome="failed", field="potassium", message=message,
        )])

    def estimate_hours(self, potassium: float, parameters: dict[str, Any]) -> float:
        return self.equation(potassium)

    def evaluate(self, parameters: dict[str, Any]) -> PMIMethodResult:
        measurement = parameters.get("potassium")
        if measurement is None:
            return self._failure("missing_input", "required:potassium", "Potassium is missing.")
        if not isinstance(measurement, dict):
            return self._failure("invalid_input", "potassium_structure", "Invalid potassium measurement.")
        if measurement.get("status") == "unavailable":
            return self._failure("missing_input", "required:potassium", "Potassium is unavailable.")
        if measurement.get("status") != "available":
            return self._failure("invalid_input", "potassium_status", "Invalid potassium availability status.")
        if measurement.get("value") is None:
            return self._failure("missing_input", "required:potassium.value", "Potassium value is missing.")
        try:
            hours = validate_estimate(self.estimate_hours(validate_potassium(measurement["value"]), parameters))
        except PotassiumInputError as exc:
            return self._failure("invalid_input", "potassium_value", str(exc))
        except FormulaDomainError as exc:
            return self._failure("invalid_domain", "pmi_domain", str(exc))

        checks = [PMICheckResult(
            id="numerical_result", outcome="passed", field="potassium.value",
            message="Calculated from vitreous potassium in mmol/L; PMI is in hours at sampling.",
        )]
        technique = measurement.get("technique") or {}
        mode = technique.get("mode")
        technique_outcome = (
            "skipped" if mode == "all" else
            ("passed" if technique.get("id") in self.techniques else "failed")
            if mode == "specific" else "unknown"
        )
        checks.append(PMICheckResult(
            id="analytical_technique", field="potassium.technique", outcome=technique_outcome,
            message=("The user explicitly selected all techniques." if mode == "all" else
                     "Required analytical technique: " + ", ".join(self.techniques) + "."),
        ))
        area = parameters.get("subject_area")
        checks.append(PMICheckResult(
            id="geographical_origin", field="subject_area",
            outcome="unknown" if area is None else "passed" if area in self.areas else "failed",
            message="Applicable subject origins: " + ", ".join(self.areas) + ".",
        ))
        criteria = parameters.get("exclusion_criteria") or {}
        for condition in self.exclusions:
            value = criteria.get(condition)
            checks.append(PMICheckResult(
                id=condition, field=f"exclusion_criteria.{condition}",
                outcome="passed" if value == "absent" else "failed" if value == "present" else "unknown",
                message=f"Required absence of {condition.replace('_', ' ')}.",
            ))
        lower, upper = self.sampling_window
        checks.append(PMICheckResult(
            id="sampling_window", outcome="unknown",
            message=f"The {lower:g}-{upper:g} hour sampling window requires Henssge and time gap.",
        ))
        return self._result("calculated", checks, hours)
