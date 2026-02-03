from pydantic import BaseModel, ConfigDict, Field


class ExportMultisigRequestSchema(BaseModel):
    """The request for `POST /v1/multisig/export`"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    address: str = Field(default=None, alias="address")
    wallet_handle_token: str = Field(default=None, alias="wallet_handle_token")
