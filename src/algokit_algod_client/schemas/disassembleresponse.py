from pydantic import BaseModel, ConfigDict, Field


class DisassembleResponseSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    result: str = Field(default=None, alias="result")
