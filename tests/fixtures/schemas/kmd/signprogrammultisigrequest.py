from pydantic import BaseModel, ConfigDict, Field


class SignProgramMultisigRequestSchema(BaseModel):
    """The request for `POST /v1/multisig/signprogram`"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    address: str = Field(alias="address")
    data: str = Field(alias="data")
    partial_multisig: "MultisigSigSchema | None" = Field(default=None, alias="partial_multisig")
    public_key: "PublicKeySchema" = Field(alias="public_key")
    use_legacy_msig: bool | None = Field(default=None, alias="use_legacy_msig")
    wallet_handle_token: str = Field(alias="wallet_handle_token")
    wallet_password: str | None = Field(default=None, alias="wallet_password")
