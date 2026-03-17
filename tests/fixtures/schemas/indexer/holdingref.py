from pydantic import BaseModel, ConfigDict, Field


class HoldingRefSchema(BaseModel):
    """HoldingRef names a holding by referring to an Address and Asset it belongs to."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    address: str = Field(alias="address")
    asset: int = Field(alias="asset")
