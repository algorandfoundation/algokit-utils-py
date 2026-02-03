from pydantic import BaseModel, ConfigDict, Field


class TransactionStateProofSchema(BaseModel):
    """Fields for a state proof transaction.

    Definition:
    data/transactions/stateproof.go : StateProofTxnFields"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    state_proof_type: int | None = Field(default=None, alias="state-proof-type")
    state_proof: "StateProofFieldsSchema | None" = Field(default=None, alias="state-proof")
    message: "IndexerStateProofMessageSchema | None" = Field(default=None, alias="message")
