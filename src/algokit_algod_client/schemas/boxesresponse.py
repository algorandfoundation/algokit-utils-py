from pydantic import BaseModel, ConfigDict, Field


class BoxesResponseSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    boxes: "list[BoxDescriptorSchema]" = Field(default=None, alias="boxes")
