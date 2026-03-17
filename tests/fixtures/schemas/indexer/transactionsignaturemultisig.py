from pydantic import BaseModel, ConfigDict, Field


class TransactionSignatureMultisigSchema(BaseModel):
    """structure holding multiple subsignatures.

    Definition:
    crypto/multisig.go : MultisigSig"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    subsignature: "list[TransactionSignatureMultisigSubsignatureSchema] | None" = Field(
        default=None, alias="subsignature"
    )
    threshold: int | None = Field(default=None, alias="threshold")
    version: int | None = Field(default=None, alias="version")
