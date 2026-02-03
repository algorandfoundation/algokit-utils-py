from pydantic import BaseModel, ConfigDict, Field


class SourceMapSchema(BaseModel):
    """Source map for the program"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    version: int = Field(default=None, alias="version")
    sources: list[str] = Field(default=None, alias="sources")
    names: list[str] = Field(default=None, alias="names")
    mappings: str = Field(default=None, alias="mappings")
