from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.pmi_draft import PMIDraftResponse
from app.schemas.pmi import PMICalculateResponse, PMISaveResponse
from app.schemas.pmi_selection import PMIResultSelection
from app.schemas.pmi_median import PMIMedianResult


class PMIChatRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    request_id: UUID
    message: str = Field(min_length=1, max_length=2000)


class PMIChatTurn(BaseModel):
    request_id: str
    user_message: str
    assistant_message: str | None = None
    status: Literal["processing", "completed", "failed"]
    created_at: datetime
    error: str | None = None
    calculation: PMICalculateResponse | None = None
    result_selection: PMIResultSelection | None = None
    median_selection: PMIResultSelection | None = None
    median_result: PMIMedianResult | None = None
    saved_calculation: PMISaveResponse | None = None


class PMIChatResponse(BaseModel):
    draft: PMIDraftResponse
    turns: list[PMIChatTurn]
