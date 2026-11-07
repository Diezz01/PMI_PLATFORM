from typing import Literal
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.pmi_case import PMICaseDraft


class PMIDraftState(BaseModel):
    model_config = ConfigDict(extra="forbid")

    data: PMICaseDraft = Field(default_factory=PMICaseDraft)
    version: int = Field(default=1, ge=1)
    status: Literal["collecting", "ready", "confirmed"] = "collecting"


class PMIDraftUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expected_version: int = Field(ge=1)
    changes: PMICaseDraft


class PMIDraftConfirmRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expected_version: int = Field(ge=1)


class PMIDraftSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    data: PMICaseDraft
    version: int
    status: Literal["collecting", "ready", "confirmed"]
    missing_required_fields: list[str]
    can_confirm: bool

class PMIDraftResponse(PMIDraftSummary):
    draft_id: str
    expires_at: datetime

class PMIDraftCalculateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expected_version: int = Field(ge=1)