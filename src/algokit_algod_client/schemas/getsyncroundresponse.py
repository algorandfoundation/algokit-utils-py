from pydantic import BaseModel, ConfigDict, Field


class GetSyncRoundResponseSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    round: int = Field(default=None, alias="round")
