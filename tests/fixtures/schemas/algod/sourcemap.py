from pydantic import BaseModel, ConfigDict, Field


class SourceMapSchema(BaseModel):
    """Source map for the program"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    version: int = Field(alias="version")
    sources: list[str] = Field(alias="sources")
    names: list[str] = Field(alias="names")
    mappings: str = Field(alias="mappings")
