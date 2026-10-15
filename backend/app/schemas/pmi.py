from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.henssge import HenssgeInput

#those are contracts that allow the LLM to execute the function requeste dby the user in Natural langauge
# The operation could be:
#- request to calcultate PMI
#- request to consider only specific results
#There are also included the contract for the response related to the request

#UPDATE: 
#each calculated prediction is associated to a user session
class PMICalculateRequest(BaseModel):
    input_data: HenssgeInput


class PMIResultResponse(BaseModel):
    method_name: str
    pmi_value: str
    input_params: dict[str, Any]
    method_version: str


class PMICalculateResponse(BaseModel):
    session_id: str
    status: Literal["calculated"]
    expires_at: datetime
    results: list[PMIResultResponse]


class PMISessionSummary(BaseModel):
    session_id: str
    status: Literal["calculated", "median_ready"]
    created_at: datetime
    expires_at: datetime
    available_methods: list[str]
    median_pmi: str | None = None


class PMISessionsResponse(BaseModel):
    sessions: list[PMISessionSummary]


class PMIMedianRequest(BaseModel):
    selected_methods: list[str] = Field(min_length=1)

    @field_validator("selected_methods")
    @classmethod
    def methods_must_be_unique(cls, methods: list[str]) -> list[str]:
        if len(methods) != len(set(methods)):
            raise ValueError("Each method can be selected only once")
        return methods


class PMIMedianResponse(BaseModel):
    session_id: str
    status: Literal["median_ready"]
    selected_methods: list[str]
    selected_results: list[PMIResultResponse]
    median_pmi: str
    expires_at: datetime


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
    median_pmi: str
    created_at: datetime

class PMIHistoryItem(BaseModel):
    calculation_id: int
    input_data: dict[str, Any]
    median_selected_methods: list[str]
    median_pmi: str
    saved_results: list[PMIResultResponse]
    created_at: datetime


class PMIHistoryResponse(BaseModel):
    calculations: list[PMIHistoryItem]
    total: int
    limit: int
    offset: int

