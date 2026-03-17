from pydantic import BaseModel, ConfigDict, Field


class CompileResponseSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    hash: str = Field(alias="hash")
    result: str = Field(alias="result")
    sourcemap: "SourceMapSchema | None" = Field(default=None, alias="sourcemap")
