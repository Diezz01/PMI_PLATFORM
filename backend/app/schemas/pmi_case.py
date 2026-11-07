from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationInfo,
    field_validator,
    model_validator,
)
from typing import Literal, Self

#In this section fixed paramter that describe analisys are reposred
ConditionState = Literal["present", "absent", "unknown"]

SubjectArea = Literal[
    "north_america",
    "usa",
    "south_america",
    "europe",
    "north_europe",
    "scandinavia",
    "west_europe",
    "china",
    "india",
    "north_africa",
]

ALLOWED_TECHNIQUES = {
    "potassium": {
        "photometer",
        "potentiometer",
        "chromatography",
        "electrophoresis",
        "turbidimetric",
        "spectrophotometry",
    },
    "hypoxanthine": {
        "hplc",
        "lc_msms",
    },
    "u_am": {
        "kinetic",
        "lc_msms",
        # electrophoresisfor Palacio (Am) method.
        "electrophoresis",
    },
}
#-------------------------------------------------------------------------

#Analitic thecnique used to nalaize biochemical parameter
#each biochemical parameter is associated with a technique
class TechniqueSelection(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        strict=True,
        str_strip_whitespace=True,
    )

    mode: Literal["specific", "all", "unknown"]
    id: str | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def check_selection(self) -> Self:
        if self.mode == "specific" and self.id is None:
            raise ValueError(
                "A specific technique requires an identifier"
            )

        if self.mode != "specific" and self.id is not None:
            raise ValueError(
                "All or unknown techniques must not have an identifier"
            )

        return self

#Biochemical data express in mmol/L
#if the data is availbale the value is mandatory
class BiochemicalMeasurement(BaseModel):
    
    model_config = ConfigDict(
        extra="forbid",
        strict=True,
        allow_inf_nan=False,
    )

    status: Literal["available", "unavailable"]
    value: float | None = None

    @model_validator(mode="after")
    def check_availability(self) -> Self:
        if self.status == "available" and self.value is None:
            raise ValueError(
                "An available measurement must have a numeric value!"
            )

        if self.status == "unavailable" and self.value is not None:
            raise ValueError(
                "An unavailable measurement must not have a value"
            )

        return self

#Biochemical parameter associated with relative Measurement
class BiochemicalMeasurementWithTechnique(BiochemicalMeasurement):

    technique: TechniqueSelection | None = None

    @model_validator(mode="after")
    def check_technique_availability(self) -> Self:
        if self.status == "available" and self.technique is None:
            raise ValueError(
                "An available measurement requires a technique selection"
            )

        if self.status == "unavailable" and self.technique is not None:
            raise ValueError(
                "An unavailable measurement must not have a technique"
            )

        return self

#represent the subject age
#if availbale, value is mandatory
class AgeData(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        strict=True,
        allow_inf_nan=False,
    )

    status: Literal["available", "unavailable"]
    #0.5 indicates 6 months for infant subject
    value: float | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def check_availability(self) -> Self:
        if self.status == "available" and self.value is None:
            raise ValueError(
                "An available age must have a numeric value"
            )

        if self.status == "unavailable" and self.value is not None:
            raise ValueError(
                "An unavailable age must not have a value"
            )

        return self

#ExclusionCriteria
class ExclusionCriteria(BaseModel):

    model_config = ConfigDict(
        extra="forbid",
        strict=True,
    )

    child: ConditionState | None = None
    decomposition: ConditionState | None = None
    vitreous_contamination: ConditionState | None = None
    sepsis: ConditionState | None = None
    electrolyte_disturbances: ConditionState | None = None
    intoxication: ConditionState | None = None
    hyperthermia: ConditionState | None = None
    hypothermia: ConditionState | None = None
    chronic_pathologies: ConditionState | None = None
    eye_trauma_or_disease: ConditionState | None = None
    kidney_disease: ConditionState | None = None
    high_blood_ammonium: ConditionState | None = None
    hydration_changes: ConditionState | None = None
    agonal_period_over_6h: ConditionState | None = None
    drowning: ConditionState | None = None
    head_trauma: ConditionState | None = None
    cerebral_hemorrhage: ConditionState | None = None

class CorrectionFactorContext(BaseModel):

    model_config = ConfigDict(
        extra="forbid",
        strict=True,
        str_strip_whitespace=True,
    )

    source: Literal["direct", "catalog_suggestion"]
    catalog_entry_id: int | None = Field(default=None, gt=0)
    description: str | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def check_catalog_reference(self) -> Self:
        if (self.source == "catalog_suggestion"and self.catalog_entry_id is None):
            raise ValueError("A catalog suggestion requires a catalog entry identifier")

        return self
    
#Represent the data collected during the conversation with the LLM
class PMICaseDraft(BaseModel):

    model_config = ConfigDict(
        extra="forbid",
        strict=True,
        allow_inf_nan=False,
    )

    rectal_temperature_c: float | None = None
    ambient_temperature_c: float | None = None
    body_mass_kg: float | None = Field(default=None,gt=0,)
    age : AgeData | None = None
    correction_factor: float | None = Field(default=None,gt=0,)
    correction_factor_context: CorrectionFactorContext | None = None
    albumin : BiochemicalMeasurement | None = None
    potassium :BiochemicalMeasurementWithTechnique | None = None
    hypoxanthine : BiochemicalMeasurementWithTechnique | None = None
    u_am : BiochemicalMeasurementWithTechnique | None = None
    subject_area : SubjectArea | None = None
    exclusion_criteria: ExclusionCriteria = Field(default_factory=ExclusionCriteria)
    time_gap_minutes: int | None = Field(
        default=None,
        ge=0,
        description=(
            "Minutes between temperature measurement "
            "and the common sampling time"
        ),
    )

    @field_validator("potassium", "hypoxanthine", "u_am")
    @classmethod
    def validate_technique_for_parameter(
        cls,
        measurement: BiochemicalMeasurementWithTechnique | None,
        info: ValidationInfo,
    ) -> BiochemicalMeasurementWithTechnique | None:
        if measurement is None or measurement.technique is None:
            return measurement

        technique = measurement.technique

        if technique.mode != "specific":
            return measurement

        allowed = ALLOWED_TECHNIQUES[info.field_name]

        if technique.id not in allowed:
            raise ValueError(
                f"Technique '{technique.id}' is not supported for "
                f"'{info.field_name}'. Allowed techniques: "
                f"{', '.join(sorted(allowed))}"
            )

        return measurement


    def get_missing_fields(self) -> list[str]:
        required_fields = (
            "rectal_temperature_c",
            "ambient_temperature_c",
            "body_mass_kg",
            "correction_factor",
        )

        return [
            field_name
            for field_name in required_fields
            if getattr(self, field_name) is None
        ]
    
    def to_complete_input(self) -> "PMICaseInput":
        """Valida la completezza senza registrare conferme o fare calcoli."""

        return PMICaseInput.model_validate(self.model_dump())

#Minimal Mandatory data to execute the calculation
class PMICaseInput(PMICaseDraft):
    rectal_temperature_c: float = Field(...)
    ambient_temperature_c: float = Field(...)
    body_mass_kg: float = Field(..., gt=0)
    correction_factor: float = Field(..., gt=0)
    