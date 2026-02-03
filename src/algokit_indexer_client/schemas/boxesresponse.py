from pydantic import BaseModel, ConfigDict, Field


class BoxesResponseSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    application_id: int = Field(default=None, alias="application-id")
    boxes: "list[BoxDescriptorSchema]" = Field(default=None, alias="boxes")
    next_token: str | None = Field(default=None, alias="next-token")
