import math
from app.schemas.pmi_results import PMICheckResult, PMIMethodResult


TIME_GAP_CHECK_ID = "time_gap_adjustment"


def apply_time_gap(
    result: PMIMethodResult,
    time_gap_minutes: int | None,
) -> PMIMethodResult:
    """Add the supplied gap to a biological estimate once."""

    if result.method_kind != "biochemical":
        return result

    if result.calculation_status != "calculated":
        return result

    if time_gap_minutes is not None:
        if (
            isinstance(time_gap_minutes, bool)
            or not isinstance(time_gap_minutes, int)
            or time_gap_minutes < 0
        ):
            raise ValueError(
                "Time gap must be a non-negative integer in minutes."
            )

    # Always use the original estimate, preventing double addition.
    sampling_hours = result.pmi_at_sampling_hours

    if sampling_hours is None:
        if result.time_reference != "sampling":
            raise ValueError(
                "A biological calculator must return a PMI "
                "referenced to sampling."
            )
        sampling_hours = result.pmi_hours

    if sampling_hours is None:
        raise ValueError("The sampling PMI is missing.")

    payload = result.model_dump(
        exclude={"applicability", "pmi_display"}
    )

    # Replace any previous adjustment check.
    checks = [
        check
        for check in payload["checks"]
        if check["id"] != TIME_GAP_CHECK_ID
    ]

    payload["pmi_at_sampling_hours"] = sampling_hours
    payload["time_gap_minutes"] = time_gap_minutes

    if time_gap_minutes is None:
        payload["pmi_hours"] = sampling_hours
        payload["time_reference"] = "sampling"

        adjustment_check = PMICheckResult(
            id=TIME_GAP_CHECK_ID,
            outcome="unknown",
            field="time_gap_minutes",
            message=(
                "Time gap was not provided. The estimate remains "
                "referenced to sampling; no zero gap was assumed."
            ),
        )

    else:
        adjusted_hours = sampling_hours + time_gap_minutes / 60.0

        if not math.isfinite(adjusted_hours) or adjusted_hours < 0:
            # Keep the original estimate, but do not expose a negative
            # final PMI or make this result eligible for the median.
            payload["calculation_status"] = "invalid_domain"
            payload["pmi_hours"] = None
            payload["time_reference"] = None

            adjustment_check = PMICheckResult(
                id=TIME_GAP_CHECK_ID,
                outcome="failed",
                field="time_gap_minutes",
                message=(
                    "Adding the time gap produced an invalid PMI. "
                    "The original estimate is retained."
                ),
            )

        else:
            payload["pmi_hours"] = adjusted_hours
            payload["time_reference"] = "time_gap_adjusted"

            adjustment_check = PMICheckResult(
                id=TIME_GAP_CHECK_ID,
                outcome="passed",
                field="time_gap_minutes",
                message=(
                    "The time gap was added to the original biological PMI."
                ),
            )

    checks.append(adjustment_check.model_dump())
    payload["checks"] = checks

    return PMIMethodResult.model_validate(payload)
