from pydantic import BaseModel, ConfigDict, Field


class AssetParamsSchema(BaseModel):
    """AssetParams specifies the parameters for an asset.

    \[apar\] when part of an AssetConfig transaction.

    Definition:
    data/transactions/asset.go : AssetParams"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    clawback: str | None = Field(default=None, alias="clawback")
    creator: str = Field(alias="creator")
    decimals: int = Field(ge=0, le=19, alias="decimals")
    default_frozen: bool | None = Field(default=None, alias="default-frozen")
    freeze: str | None = Field(default=None, alias="freeze")
    manager: str | None = Field(default=None, alias="manager")
    metadata_hash: str | None = Field(default=None, alias="metadata-hash")
    name: str | None = Field(default=None, alias="name")
    name_b64: str | None = Field(default=None, alias="name-b64")
    reserve: str | None = Field(default=None, alias="reserve")
    total: int = Field(alias="total")
    unit_name: str | None = Field(default=None, alias="unit-name")
    unit_name_b64: str | None = Field(default=None, alias="unit-name-b64")
    url: str | None = Field(default=None, alias="url")
    url_b64: str | None = Field(default=None, alias="url-b64")
