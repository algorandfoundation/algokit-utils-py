from pydantic import BaseModel, ConfigDict, Field


class TransactionKeyregSchema(BaseModel):
    """Fields for a keyreg transaction.

    Definition:
    data/transactions/keyreg.go : KeyregTxnFields"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    non_participation: bool | None = Field(default=None, alias="non-participation")
    selection_participation_key: str | None = Field(default=None, alias="selection-participation-key")
    vote_first_valid: int | None = Field(default=None, alias="vote-first-valid")
    vote_key_dilution: int | None = Field(default=None, alias="vote-key-dilution")
    vote_last_valid: int | None = Field(default=None, alias="vote-last-valid")
    vote_participation_key: str | None = Field(default=None, alias="vote-participation-key")
    state_proof_key: str | None = Field(default=None, alias="state-proof-key")
