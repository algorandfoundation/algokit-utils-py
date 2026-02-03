from pydantic import BaseModel, ConfigDict, Field


class GenesisSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    alloc: "list[GenesisAllocationSchema]" = Field(default=None, alias="alloc")
    comment: str | None = Field(default=None, alias="comment")
    devmode: bool | None = Field(default=None, alias="devmode")
    fees: str = Field(default=None, alias="fees")
    id: str = Field(default=None, alias="id")
    network: str = Field(default=None, alias="network")
    proto: str = Field(default=None, alias="proto")
    rwd: str = Field(default=None, alias="rwd")
    timestamp: int | None = Field(default=None, alias="timestamp")
