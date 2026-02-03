from pydantic import BaseModel, ConfigDict, Field


class GetBlockTimeStampOffsetResponseSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    offset: int = Field(default=None, alias="offset")
