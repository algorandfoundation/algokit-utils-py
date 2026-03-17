from pydantic import BaseModel, ConfigDict, Field


class BoxReferenceSchema(BaseModel):
    """References a box of an application."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    app: int = Field(alias="app")
    name: str = Field(alias="name")
