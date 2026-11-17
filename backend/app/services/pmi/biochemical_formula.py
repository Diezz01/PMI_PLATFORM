"""Common pipeline for single- and multi-analyte PMI equations.

Equations receive validated numeric values keyed by input path. They return
raw hours; the orchestrator applies the time gap and sampling-window checks.
No implicit unit conversion or substitution between urea and ammonium occurs.
"""
import math
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Literal

from app.schemas.pmi_case import ALLOWED_TECHNIQUES, ExclusionCriteria, SubjectArea
from app.schemas.pmi_results import PMICheckResult, PMIMethodResult
from app.services.pmi.base_calculator import PMICalculator
from typing import get_args


class BiochemicalInputError(ValueError):
    pass


class FormulaDomainError(ValueError):
    pass


def validate_number(value: Any, label: str, *, nonnegative: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise BiochemicalInputError(f"{label} must be a number.")
    if not math.isfinite(value) or (nonnegative and value < 0):
        raise BiochemicalInputError(f"{label} must be finite" + (" and non-negative." if nonnegative else "."))
    return value


def validate_estimate(hours: float) -> float:
    if not math.isfinite(hours) or hours < 0:
        raise FormulaDomainError("The equation produced a negative or non-finite PMI.")
    return hours


@dataclass(frozen=True)
class MeasurementRequirement:
    field: Literal["potassium", "hypoxanthine", "albumin", "u_am"]
    unit: Literal["mmol_l", "g_l", "mg_dl"]
    techniques: tuple[str, ...] = ()
    analyte: Literal["urea", "ammonium"] | None = None

    def __post_init__(self):
        expected_unit = {"potassium": "mmol_l", "hypoxanthine": "mmol_l", "albumin": "g_l"}
        if self.field == "u_am":
            expected = {"urea": "mg_dl", "ammonium": "mmol_l"}.get(self.analyte)
        else:
            expected = expected_unit.get(self.field)
            if self.analyte is not None:
                raise ValueError("Only U/Am accepts an analyte discriminator.")
        if expected is None or self.unit != expected:
            raise ValueError(f"Invalid unit or analyte configuration for {self.field}.")
        if not isinstance(self.techniques, tuple):
            raise ValueError("Techniques must be a tuple of identifiers.")
        allowed = ALLOWED_TECHNIQUES.get(self.field, set())
        if (allowed and not self.techniques) or not set(self.techniques).issubset(allowed):
            raise ValueError(f"Invalid analytical techniques for {self.field}.")


class BiochemicalFormula(PMICalculator):
    version = "development-3"
    method_kind = "biochemical"

    def __init__(
        self, identifier: str, title: str,
        equation: Callable[[dict[str, float]], float], *,
        measurements: tuple[MeasurementRequirement, ...],
        areas: tuple[str, ...], exclusions: tuple[str, ...] = (),
        sampling_window: tuple[float, float] | None = None,
        required_values: tuple[str, ...] = (),
    ):
        if not measurements or len({r.field for r in measurements}) != len(measurements):
            raise ValueError("Specify unique measurement fields for each formula.")
        if not isinstance(areas, tuple) or not areas or not set(areas).issubset(get_args(SubjectArea)):
            raise ValueError("Specify valid subject origins explicitly.")
        if not isinstance(exclusions, tuple) or not set(exclusions).issubset(ExclusionCriteria.model_fields):
            raise ValueError("Invalid exclusion criteria configuration.")
        if sampling_window is not None:
            lower, upper = sampling_window
            if not (math.isfinite(lower) and math.isfinite(upper) and 0 <= lower <= upper):
                raise ValueError("Invalid sampling window.")
        if set(required_values) & {r.field for r in measurements}:
            raise ValueError("Scalar paths must not duplicate measurement fields.")
        self.identifier, self.title, self.equation = identifier, title, equation
        self.measurements, self.required_values = measurements, required_values
        self.areas, self.exclusions, self.sampling_window = areas, exclusions, sampling_window

    @property
    def name(self) -> str:
        return self.identifier

    @property
    def required_parameters(self) -> list[str]:
        return [r.field for r in self.measurements] + list(self.required_values)

    def _result(self, status, checks, hours=None):
        return PMIMethodResult(
            method_id=self.name, method_name=self.title, method_version=self.version,
            method_kind=self.method_kind, calculation_status=status, pmi_hours=hours,
            time_reference="sampling" if hours is not None else None, checks=checks,
        )

    def _failure(self, status, check_id, message, field=None):
        return self._result(status, [PMICheckResult(
            id=check_id, outcome="failed", field=field, message=message,
        )])

    def estimate(self, values: dict[str, float], parameters: dict[str, Any]) -> float:
        return self.equation(values)

    def evaluate(self, parameters: dict[str, Any]) -> PMIMethodResult:
        values, checks, problems = {}, [], []
        for requirement in self.measurements:
            field = requirement.field
            measurement = parameters.get(field)
            if measurement is None or (isinstance(measurement, dict) and measurement.get("status") == "unavailable"):
                problems.append(("missing_input", f"required:{field}", field, f"{field} is missing or unavailable."))
                continue
            if not isinstance(measurement, dict) or measurement.get("status") != "available":
                problems.append(("invalid_input", f"structure:{field}", field, f"Invalid {field} measurement."))
                continue
            if measurement.get("value") is None:
                problems.append(("missing_input", f"required:{field}.value", field, f"{field} value is missing."))
                continue
            # Legacy K+/Hx inputs had a fixed mmol/L convention. Old albumin
            # and U/Am values require re-entry with explicit units/identity.
            unit = measurement.get("unit")
            if unit is None and field in {"potassium", "hypoxanthine"}:
                unit = "mmol_l"
            if unit != requirement.unit:
                problems.append(("missing_input" if unit is None else "invalid_input",
                                 f"unit:{field}", field, f"{field} requires unit {requirement.unit}; no conversion was applied."))
                continue
            if requirement.analyte and measurement.get("analyte") != requirement.analyte:
                problems.append(("missing_input" if measurement.get("analyte") is None else "invalid_input",
                                 f"analyte:{field}", field, f"{field} must explicitly contain {requirement.analyte}."))
                continue
            try:
                values[field] = validate_number(measurement["value"], field, nonnegative=True)
            except BiochemicalInputError as exc:
                problems.append(("invalid_input", f"value:{field}", field, str(exc)))
                continue
            if requirement.techniques:
                technique = measurement.get("technique") or {}
                mode = technique.get("mode")
                outcome = ("skipped" if mode == "all" else
                           ("passed" if technique.get("id") in requirement.techniques else "failed")
                           if mode == "specific" else "unknown")
                checks.append(PMICheckResult(
                    id=f"analytical_technique:{field}", field=f"{field}.technique", outcome=outcome,
                    message=("The user explicitly selected all techniques for " + field + "." if mode == "all" else
                             f"{field} requires: {', '.join(requirement.techniques)}."),
                ))

        for path in self.required_values:
            value = parameters
            for part in path.split("."):
                value = value.get(part) if isinstance(value, dict) else None
            try:
                if value is None:
                    problems.append(("missing_input", f"required:{path}", path, f"{path} is missing."))
                else:
                    values[path] = validate_number(value, path)
            except BiochemicalInputError as exc:
                problems.append(("invalid_input", f"value:{path}", path, str(exc)))
        if problems:
            return self._result(
                "invalid_input" if any(p[0] == "invalid_input" for p in problems) else "missing_input",
                [PMICheckResult(id=identifier, outcome="failed", field=field, message=message)
                 for _, identifier, field, message in problems],
            )
        try:
            hours = validate_estimate(self.estimate(values, parameters))
        except BiochemicalInputError as exc:
            return self._failure("invalid_input", "numeric_input", str(exc))
        except (FormulaDomainError, ZeroDivisionError, OverflowError) as exc:
            return self._failure("invalid_domain", "pmi_domain", str(exc))
        checks.insert(0, PMICheckResult(id="numerical_result", outcome="passed",
                                      message="The equation produced a finite non-negative PMI in hours."))
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
        if self.sampling_window is not None:
            lower, upper = self.sampling_window
            checks.append(PMICheckResult(id="sampling_window", outcome="unknown",
                                        message=f"The {lower:g}-{upper:g} hour sampling window requires Henssge and time gap."))
        return self._result("calculated", checks, hours)
