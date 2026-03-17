from pydantic import BaseModel, ConfigDict, Field


class CreateWalletRequestSchema(BaseModel):
    """The request for `POST /v1/wallet`"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    master_derivation_key: "MasterDerivationKeySchema | None" = Field(default=None, alias="master_derivation_key")
    wallet_driver_name: str | None = Field(default=None, alias="wallet_driver_name")
    wallet_name: str = Field(alias="wallet_name")
    wallet_password: str = Field(alias="wallet_password")
