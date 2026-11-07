from typing import Annotated, Literal, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    computed_field,
    model_validator,
)


MethodId = Annotated[str, Field(min_length=1)]

#Method selected by the user
class PMIMedianSelection(BaseModel):

    model_config = ConfigDict(
        extra="forbid",
        strict=True,
        allow_inf_nan=False,
    )

    selected_method_ids: list[MethodId]
    acknowledged_warning_method_ids: list[MethodId] = Field(default_factory=list,)

    @model_validator(mode="after")
    def check_selection(self) -> Self:
        selected = self.selected_method_ids
        acknowledged = self.acknowledged_warning_method_ids

        if len(selected) != len(set(selected)):
            raise ValueError("Each method can be selected only once")

        if len(acknowledged) != len(set(acknowledged)):
            raise ValueError("Each warning acknowledgement can appear only once")

        if not set(acknowledged).issubset(selected):
            raise ValueError("Warning acknowledgements must refer to selected methods")
        return self

#Mendian refers to a specific session
class PMIMedianSelectionRequest(PMIMedianSelection):
    expected_version: int = Field(ge=1)

#median Backend result
class PMIMedianResult(PMIMedianSelection):
    status: Literal["calculated", "not_calculated"]
    pmi_hours: float | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def check_result_consistency(self) -> Self:
        if self.status == "calculated":
            if not self.selected_method_ids:
                raise ValueError("A calculated median requires at least one method")

            if self.pmi_hours is None:
                raise ValueError("A calculated median requires a numeric PMI")

        else:
            if self.pmi_hours is not None:
                raise ValueError("An uncalculated median must not contain a PMI value")

            if self.selected_method_ids:
                raise ValueError("An uncalculated median must have an empty selection")

        return self

    @computed_field
    @property
    def pmi_display(self) -> str | None:
        if self.pmi_hours is None:
            return None

        total_minutes = int(self.pmi_hours * 60 + 0.5)
        hours, minutes = divmod(total_minutes, 60)

        return f"{hours:02d}:{minutes:02d}"