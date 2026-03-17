from pydantic import BaseModel, ConfigDict, Field


class TransactionSignatureLogicsigSchema(BaseModel):
    """\[lsig\] Programatic transaction signature.

    Definition:
    data/transactions/logicsig.go"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    args: list[str] | None = Field(default=None, alias="args")
    logic: str = Field(alias="logic")
    multisig_signature: "TransactionSignatureMultisigSchema | None" = Field(default=None, alias="multisig-signature")
    logic_multisig_signature: "TransactionSignatureMultisigSchema | None" = Field(
        default=None, alias="logic-multisig-signature"
    )
    signature: str | None = Field(default=None, alias="signature")
