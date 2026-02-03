from pydantic import BaseModel, ConfigDict, Field


class BoxDescriptorSchema(BaseModel):
    """Box descriptor describes an app box without a value."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    name: str = Field(default=None, alias="name")
