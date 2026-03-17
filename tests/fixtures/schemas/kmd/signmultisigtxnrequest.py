from pydantic import BaseModel, ConfigDict, Field


class SignMultisigTxnRequestSchema(BaseModel):
    """The request for `POST /v1/multisig/sign`"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    partial_multisig: "MultisigSigSchema | None" = Field(default=None, alias="partial_multisig")
    public_key: "PublicKeySchema" = Field(alias="public_key")
    signer: "DigestSchema | None" = Field(default=None, alias="signer")
    transaction: str = Field(alias="transaction")
    wallet_handle_token: str = Field(alias="wallet_handle_token")
    wallet_password: str | None = Field(default=None, alias="wallet_password")
