import logging
import math
from statistics import median
from typing import Any

from app.schemas.pmi_results import PMICheckResult, PMIMethodResult
from app.services.pmi.registry import registry
from app.services.pmi.time_reference import apply_time_gap


logger = logging.getLogger(__name__)


class PMIOrchestrator:
    @staticmethod
    def _parameter_is_missing(input_data: dict[str, Any],parameter: str) -> bool:
        value: Any = input_data

        for part in parameter.split("."):
            if not isinstance(value, dict) or part not in value:
                return True

            value = value[part]

        if value is None:
            return True

        if isinstance(value, dict):
            if value.get("status") == "unavailable":
                return True

            if (
                value.get("status") == "available"
                and value.get("value") is None
            ):
                return True

        return False

    def evaluate(self,input_data: dict[str, Any]) -> list[PMIMethodResult]:
        """Valuta tutti i metodi senza perdere gli esiti non calcolabili."""

        results: list[PMIMethodResult] = []

        for method in registry.get_all_calculators():
            try:
                missing_parameters = [
                    parameter
                    for parameter in method.required_parameters
                    if self._parameter_is_missing(input_data, parameter)
                ]

                if missing_parameters:
                    results.append(
                        PMIMethodResult(
                            method_id=method.name,
                            method_name=method.name,
                            method_version=method.version,
                            method_kind=method.method_kind,
                            calculation_status="missing_input",
                            pmi_hours=None,
                            time_reference=None,
                            checks=[
                                PMICheckResult(
                                    id=f"required:{parameter}",
                                    outcome="failed",
                                    field=parameter,
                                    message=(
                                        f"Required parameter "
                                        f"'{parameter}' is not available"
                                    ),
                                )
                                for parameter in missing_parameters
                            ],
                        )
                    )
                    continue

                result = method.evaluate(input_data)

                if not isinstance(result, PMIMethodResult):
                    raise TypeError(
                        "Calculator must return PMIMethodResult"
                    )

                if (
                    result.method_id != method.name
                    or result.method_version != method.version
                    or result.method_kind != method.method_kind
                ):
                    raise ValueError(
                        "Result metadata does not match the calculator"
                    )

                result = apply_time_gap(
                    result,
                    input_data.get("time_gap_minutes"),
                )

                results.append(result)

            except Exception as exc:
                logger.error(
                    "PMI method %s failed with %s",
                    method.name,
                    type(exc).__name__,
                )

                results.append(
                    PMIMethodResult(
                        method_id=method.name,
                        method_name=method.name,
                        method_version=method.version,
                        method_kind=method.method_kind,
                        calculation_status="error",
                        pmi_hours=None,
                        time_reference=None,
                        checks=[
                            PMICheckResult(
                                id="calculation_error",
                                outcome="failed",
                                field=None,
                                message=(
                                    "The method could not complete the calculation"
                                ),
                            )
                        ],
                    )
                )

        # All methods are available here, regardless of registry order.
        henssge = next((r for r in results if r.method_kind == "henssge"), None)
        gap = input_data.get("time_gap_minutes")
        sampling_hours = None
        if (
            henssge is not None
            and henssge.calculation_status == "calculated"
            and henssge.pmi_hours is not None
            and henssge.time_reference == "temperature_measurement"
            and not any(c.outcome == "failed" for c in henssge.checks)
            and isinstance(gap, int) and not isinstance(gap, bool) and gap >= 0
        ):
            try:
                estimate = henssge.pmi_hours + gap / 60.0
                if math.isfinite(estimate) and estimate >= 0:
                    sampling_hours = estimate
            except OverflowError:
                pass

        for result in results:
            method = registry.get_calculator(result.method_id)
            window = getattr(method, "sampling_window", None)
            if window is None or result.calculation_status != "calculated":
                continue
            lower, upper = window
            check = PMICheckResult(
                id="sampling_window",
                field="time_gap_minutes",
                outcome=("unknown" if sampling_hours is None else
                         "passed" if lower <= sampling_hours <= upper else "failed"),
                message=(
                    f"The {lower:g}-{upper:g} hour sampling window cannot be checked: "
                    "a usable Henssge estimate and an explicit time gap are required."
                    if sampling_hours is None else
                    f"Henssge plus time gap estimates {sampling_hours:.2f} hours "
                    f"at sampling; the allowed window is {lower:g}-{upper:g} hours. "
                    "This is an estimate-based compatibility check."
                ),
            )
            result.checks = [c for c in result.checks if c.id != check.id] + [check]

        return results

    def calculate(
        self,
        input_data: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Adattatore temporaneo per le API esistenti."""

        evaluated_results = self.evaluate(input_data)

        results = [
            {
                "method_name": result.method_id,
                "pmi_value": result.pmi_hours,
                "input_params": input_data,
                "method_version": result.method_version,
            }
            for result in evaluated_results
            if result.calculation_status == "calculated"
        ]

        if not results:
            raise ValueError(
                "No PMI method produced a result "
                "with the provided parameters"
            )

        return results

    def calculate_median(
        self,
        results: list[dict[str, Any]],
    ) -> float:
        """Compatibilità temporanea con il vecchio percorso mediana."""

        if not results:
            raise ValueError(
                "At least one PMI result is required"
            )

        return float(
            median(result["pmi_value"] for result in results)
        )
