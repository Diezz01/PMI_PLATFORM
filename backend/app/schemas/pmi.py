from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.pmi_case import PMICaseInput
from app.schemas.pmi_results import PMIMethodResult
from app.schemas.pmi_median import (
    PMIMedianResult,
    PMIMedianSelectionRequest,
)

class PMICorrectiveFactorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    cf_value: float
    dry_clothing_or_covering: str | None
    in_air: str | None
    wet_through_clothing_or_covering_or_wet_body_surface: str | None
    water: str | None


class PMICorrectiveFactorsResponse(BaseModel):
    correction_factors: list[PMICorrectiveFactorResponse]


#those are contracts that allow the LLM to execute the function requeste dby the user in Natural langauge
# The operation could be:
#- request to calcultate PMI
#- request to consider only specific results
#There are also included the contract for the response related to the request

#UPDATE: 
#each calculated prediction is associated to a user session
class PMICalculateRequest(BaseModel):
    input_data: PMICaseInput

class PMIResultResponse(BaseModel):
    method_name: str
    pmi_value: str
    input_params: dict[str, Any]
    method_version: str


class PMICalculateResponse(BaseModel):
    session_id: str
    source_draft: dict[str, Any] | None = None
    status: Literal["calculated"]
    expires_at: datetime
    results: list[PMIResultResponse]
    evaluated_results: list[PMIMethodResult] = Field(default_factory=list)
    version: int


class PMISessionSummary(BaseModel):
    session_id: str
    status: Literal["calculated", "median_ready"]
    created_at: datetime
    expires_at: datetime
    available_methods: list[str]
    median_pmi: str | None = None
    version: int


class PMISessionsResponse(BaseModel):
    sessions: list[PMISessionSummary]


class PMIMedianRequest(PMIMedianSelectionRequest):
    pass


class PMIMedianResponse(BaseModel):
    session_id: str
    status: Literal["calculated", "median_ready"]
    median: PMIMedianResult
    expires_at: datetime
    version: int


class PMISaveRequest(BaseModel):
    selected_methods: list[str] = Field(min_length=1)

    @field_validator("selected_methods")
    @classmethod
    def methods_must_be_unique(cls, methods: list[str]) -> list[str]:
        if len(methods) != len(set(methods)):
            raise ValueError("Each method can be selected only once")
        return methods


class PMISaveResponse(BaseModel):
    calculation_id: int #identifier of a single computation of pmi
    session_id: str #identifier of session of computations
    saved_results: list[PMIResultResponse]
    median_selected_methods: list[str]
    median_pmi: str | None
    evaluation_snapshot: dict[str, Any] | None = None
    created_at: datetime

class PMIHistoryItem(BaseModel):
    calculation_id: int
    input_data: dict[str, Any]
    median_selected_methods: list[str]
    median_pmi: str | None
    evaluation_snapshot: dict[str, Any] | None = None
    saved_results: list[PMIResultResponse]
    created_at: datetime


class PMIHistoryResponse(BaseModel):
    calculations: list[PMIHistoryItem]
    total: int
    limit: int
    offset: int

