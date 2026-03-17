from pydantic import BaseModel, ConfigDict, Field


class BlockHashResponseSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    block_hash: str = Field(alias="blockHash")
