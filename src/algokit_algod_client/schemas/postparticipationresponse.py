from pydantic import BaseModel, ConfigDict, Field


class PostParticipationResponseSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    partId: str = Field(default=None, alias="partId")
