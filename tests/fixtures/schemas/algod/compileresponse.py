from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class CompileResponseSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    hash: str = Field(default=None, alias="hash")
    result: str = Field(default=None, alias="result")
    sourcemap: "SourceMapSchema | None" = Field(default=None, alias="sourcemap")
