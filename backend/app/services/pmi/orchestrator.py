import logging
from statistics import median
from typing import Any

from app.schemas.pmi_results import PMICheckResult, PMIMethodResult
from app.services.pmi.registry import registry


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