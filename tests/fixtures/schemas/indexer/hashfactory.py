from pydantic import BaseModel, ConfigDict, Field


class HashFactorySchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    hash_type: int | None = Field(default=None, alias="hash-type")
