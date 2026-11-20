from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class PMIResultSelection(BaseModel):
    model_config = ConfigDict(extra="forbid")
    session_id: str
    source_draft_id: str
    source_draft_version: int = Field(ge=1)
    status: Literal["empty", "selected", "awaiting_warning_confirmation"] = "empty"
    selected_method_ids: list[str] = Field(default_factory=list)
    acknowledged_warning_method_ids: list[str] = Field(default_factory=list)
    pending_method_ids: list[str] = Field(default_factory=list)
    pending_warning_method_ids: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_selection(self):
        for values in (self.selected_method_ids, self.acknowledged_warning_method_ids,
                       self.pending_method_ids, self.pending_warning_method_ids):
            if len(values) != len(set(values)):
                raise ValueError("Duplicate method identifiers.")
        if not set(self.acknowledged_warning_method_ids) <= set(self.selected_method_ids):
            raise ValueError("Acknowledgements must refer to selected methods.")
        if not set(self.pending_warning_method_ids) <= set(self.pending_method_ids):
            raise ValueError("Pending warnings must refer to pending methods.")
        if self.status == "awaiting_warning_confirmation":
            if not self.pending_method_ids or not self.pending_warning_method_ids:
                raise ValueError("A pending selection requires pending warnings.")
        elif self.pending_method_ids or self.pending_warning_method_ids:
            raise ValueError("Only a pending selection can contain pending methods.")
        if self.status == "selected" and not self.selected_method_ids:
            raise ValueError("A selected state requires results.")
        return self
