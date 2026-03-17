from pydantic import BaseModel, ConfigDict, Field


class DryrunStateSchema(BaseModel):
    """Stores the TEAL eval step data"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    line: int = Field(alias="line")
    pc: int = Field(alias="pc")
    stack: "list[TealValueSchema]" = Field(alias="stack")
    scratch: "list[TealValueSchema] | None" = Field(default=None, alias="scratch")
    error: str | None = Field(default=None, alias="error")
