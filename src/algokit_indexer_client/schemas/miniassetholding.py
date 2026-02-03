from pydantic import BaseModel, ConfigDict, Field


class MiniAssetHoldingSchema(BaseModel):
    """A simplified version of AssetHolding"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    address: str = Field(default=None, alias="address")
    amount: int = Field(default=None, alias="amount")
    is_frozen: bool = Field(default=None, alias="is-frozen")
    deleted: bool | None = Field(default=None, alias="deleted")
    opted_in_at_round: int | None = Field(default=None, alias="opted-in-at-round")
    opted_out_at_round: int | None = Field(default=None, alias="opted-out-at-round")
