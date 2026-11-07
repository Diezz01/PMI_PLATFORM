import math
from statistics import median

from app.schemas.pmi_median import (
    PMIMedianResult,
    PMIMedianSelection,
)
from app.schemas.pmi_results import PMIMethodResult

#Calculate the median of selected results
class PMIMedianService:
    def calculate(self,results: list[PMIMethodResult],selection: PMIMedianSelection) -> PMIMedianResult:
        if not selection.selected_method_ids:
            return PMIMedianResult(
                status="not_calculated",
                selected_method_ids=[],
                acknowledged_warning_method_ids=[],
                pmi_hours=None,
            )

        results_by_id: dict[str, PMIMethodResult] = {}

        #Check for duplicates
        for result in results:
            if result.method_id in results_by_id:
                raise ValueError(f"Duplicate result identifier: {result.method_id}")
            results_by_id[result.method_id] = result

        values: list[float] = []
        warning_methods: set[str] = set()

        for method_id in selection.selected_method_ids:
            result = results_by_id.get(method_id)

            if result is None:
                raise ValueError(f"Method '{method_id}' is not available in this session")

            if result.method_kind == "henssge":
                raise ValueError("Henssge cannot be included in the median")

            if result.method_kind == "mock":
                raise ValueError(
                    "Development mock results cannot be included "
                    "in the median"
                )

            if (
                result.calculation_status != "calculated"
                or result.pmi_hours is None
            ):
                raise ValueError(f"Method '{method_id}' has no calculated PMI")

            if (
                not math.isfinite(result.pmi_hours)
                or result.pmi_hours < 0
            ):
                raise ValueError(f"Method '{method_id}' has an invalid PMI value")

            if result.time_reference != "sampling":
                raise ValueError("Method '{method_id}' must have a PMI referenced to the sampling time")

            if result.applicability in {"unmatched", "unverified"}:
                warning_methods.add(method_id)

            values.append(result.pmi_hours)

        acknowledged = set(selection.acknowledged_warning_method_ids)

        if acknowledged != warning_methods:
            raise ValueError(
                "Warning acknowledgements must match exactly "
                "the selected methods with applicability warnings"
            )

        median_hours = float(median(values))

        if not math.isfinite(median_hours):
            raise ValueError(
                "The median cannot be represented as a finite number"
            )

        return PMIMedianResult(
            status="calculated",
            selected_method_ids=selection.selected_method_ids.copy(),
            acknowledged_warning_method_ids=(
                selection.acknowledged_warning_method_ids.copy()
            ),
            pmi_hours=median_hours,
        )