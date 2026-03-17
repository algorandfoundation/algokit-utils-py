from pydantic import BaseModel, ConfigDict, Field


class WalletSchema(BaseModel):
    """Wallet is the API's representation of a wallet"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    driver_name: str = Field(alias="driver_name")
    driver_version: int = Field(alias="driver_version")
    id: str = Field(alias="id")
    mnemonic_ux: bool = Field(alias="mnemonic_ux")
    name: str = Field(alias="name")
    supported_txs: "list[TxTypeSchema]" = Field(alias="supported_txs")
