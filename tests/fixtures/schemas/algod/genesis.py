from pydantic import BaseModel, ConfigDict, Field


class GenesisSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    alloc: "list[GenesisAllocationSchema]" = Field(alias="alloc")
    comment: str | None = Field(default=None, alias="comment")
    devmode: bool | None = Field(default=None, alias="devmode")
    fees: str = Field(alias="fees")
    id: str = Field(alias="id")
    network: str = Field(alias="network")
    proto: str = Field(alias="proto")
    rwd: str = Field(alias="rwd")
    timestamp: int | None = Field(default=None, alias="timestamp")
