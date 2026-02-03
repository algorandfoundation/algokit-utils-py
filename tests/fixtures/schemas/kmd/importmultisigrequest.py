from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class ImportMultisigRequestSchema(BaseModel):
    """The request for `POST /v1/multisig/import`"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    multisig_version: int = Field(default=None, alias="multisig_version")
    pks: "list[PublicKeySchema]" = Field(default=None, alias="pks")
    threshold: int = Field(default=None, alias="threshold")
    wallet_handle_token: str = Field(default=None, alias="wallet_handle_token")
