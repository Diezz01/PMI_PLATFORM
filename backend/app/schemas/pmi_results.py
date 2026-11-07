from typing import Literal, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    computed_field,
    model_validator,
)


class PMICheckResult(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        strict=True,
    )

    id: str = Field(min_length=1)
    outcome: Literal["passed", "failed", "unknown", "skipped"]
    field: str | None = None
    message: str = Field(min_length=1)

#result of a single method
class PMIMethodResult(BaseModel):

    model_config = ConfigDict(
        extra="forbid",
        strict=True,
        allow_inf_nan=False,
    )

    method_id: str = Field(min_length=1)
    method_name: str = Field(min_length=1)
    method_version: str = Field(min_length=1)
    method_kind: Literal["henssge", "biochemical", "mock"]
    # Riferimento temporale del valore finale contenuto in pmi_hours.
    # None indica che non è ancora stato determinato.
    time_reference: Literal["temperature_measurement","sampling"] | None = None

    calculation_status: Literal[
        "calculated",
        "missing_input",
        "invalid_input",
        "invalid_domain",
        "blocked",
        "error",
    ]

    pmi_hours: float | None = Field(default=None, ge=0)

    # Missed calculation
    checks: list[PMICheckResult] = Field(min_length=1)

    @model_validator(mode="after")
    def check_result_consistency(self) -> Self:
        if self.calculation_status == "calculated":
            if self.pmi_hours is None:
                raise ValueError(
                    "A calculated result requires a numeric PMI"
                )
        elif self.pmi_hours is not None:
            raise ValueError(
                "An unsuccessful calculation must not contain a PMI value"
            )

        return self

    @computed_field
    @property
    def applicability(
        self,
    ) -> Literal[
        "matched",
        "unmatched",
        "unverified",
        "not_evaluated",
    ]:
        if self.calculation_status != "calculated":
            return "not_evaluated"

        outcomes = {check.outcome for check in self.checks}

        if "failed" in outcomes:
            return "unmatched"

        if "unknown" in outcomes:
            return "unverified"

        return "matched"

    @computed_field
    @property
    def pmi_display(self) -> str | None:
        if self.pmi_hours is None:
            return None

        total_minutes = int(self.pmi_hours * 60 + 0.5)
        hours, minutes = divmod(total_minutes, 60)

        return f"{hours:02d}:{minutes:02d}"