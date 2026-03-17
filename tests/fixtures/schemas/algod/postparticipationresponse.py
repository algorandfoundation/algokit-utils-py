from pydantic import BaseModel, ConfigDict, Field


class PostParticipationResponseSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    part_id: str = Field(alias="partId")
