from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class DryrunStateSchema(BaseModel):
    """Stores the TEAL eval step data"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    line: int = Field(default=None, alias="line")
    pc: int = Field(default=None, alias="pc")
    stack: "list[TealValueSchema]" = Field(default=None, alias="stack")
    scratch: "list[TealValueSchema] | None" = Field(default=None, alias="scratch")
    error: str | None = Field(default=None, alias="error")
