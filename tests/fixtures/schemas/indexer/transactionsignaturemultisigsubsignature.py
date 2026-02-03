from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class TransactionSignatureMultisigSubsignatureSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    public_key: str | None = Field(default=None, alias="public-key")
    signature: str | None = Field(default=None, alias="signature")
