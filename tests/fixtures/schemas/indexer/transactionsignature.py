from pydantic import BaseModel, ConfigDict, Field


class TransactionSignatureSchema(BaseModel):
    """Validation signature associated with some data. Only one of the signatures should be provided."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    logicsig: "TransactionSignatureLogicsigSchema | None" = Field(default=None, alias="logicsig")
    multisig: "TransactionSignatureMultisigSchema | None" = Field(default=None, alias="multisig")
    sig: str | None = Field(default=None, alias="sig")
