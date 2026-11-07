from pydantic import BaseModel, ConfigDict


class ReadDraftArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")