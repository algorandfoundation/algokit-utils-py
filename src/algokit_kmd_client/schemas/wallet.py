from pydantic import BaseModel, ConfigDict, Field


class WalletSchema(BaseModel):
    """Wallet is the API's representation of a wallet"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    driver_name: str = Field(default=None, alias="driver_name")
    driver_version: int = Field(default=None, alias="driver_version")
    id: str = Field(default=None, alias="id")
    mnemonic_ux: bool = Field(default=None, alias="mnemonic_ux")
    name: str = Field(default=None, alias="name")
    supported_txs: "list[TxTypeSchema]" = Field(default=None, alias="supported_txs")
