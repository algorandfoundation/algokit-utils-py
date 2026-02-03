from pydantic import BaseModel, ConfigDict, Field


class BoxReferenceSchema(BaseModel):
    """BoxReference names a box by its name and the application ID it belongs to."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    app: int = Field(default=None, alias="app")
    name: str = Field(default=None, alias="name")
