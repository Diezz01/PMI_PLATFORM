from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


class HenssgeInput(BaseModel):
    """Input ranges follow PMI Calculator 1.1, pages 2-4.

    Database membership of the correction factor is checked by PMIService.
    Suitability for the conditions of a particular case is not checked here.
    """

    model_config = ConfigDict(extra="forbid", strict=True, allow_inf_nan=False)

    rectal_temperature_c: float = Field(
        ge=0, le=37, description="Rectal temperature in degrees Celsius (Tb).",
    )
    ambient_temperature_c: float = Field(
        ge=-10, le=45, description="Ambient temperature in degrees Celsius (Te).",
    )
    body_mass_kg: float = Field(
        ge=10, le=200, description="Body mass in kilograms (W).",
    )
    correction_factor: float = Field(
        gt=0,
        description="Positive dimensionless factor; must exist in pmi_corrective_factors.cf_value.",
    )

    @model_validator(mode="after")
    def check_temperature_order(self) -> Self:
        #I.
        if self.rectal_temperature_c < self.ambient_temperature_c:
            raise ValueError(
                "Rectal temperature must be greater than or equal to Ambient Temperature c"
            )
        return self
