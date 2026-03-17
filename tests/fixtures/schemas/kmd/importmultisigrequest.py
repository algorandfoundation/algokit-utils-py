from pydantic import BaseModel, ConfigDict, Field


class ImportMultisigRequestSchema(BaseModel):
    """The request for `POST /v1/multisig/import`"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    multisig_version: int = Field(alias="multisig_version")
    pks: "list[PublicKeySchema]" = Field(alias="pks")
    threshold: int = Field(alias="threshold")
    wallet_handle_token: str = Field(alias="wallet_handle_token")
