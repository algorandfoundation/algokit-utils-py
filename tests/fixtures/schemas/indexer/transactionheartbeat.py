from pydantic import BaseModel, ConfigDict, Field


class TransactionHeartbeatSchema(BaseModel):
    """Fields for a heartbeat transaction.

    Definition:
    data/transactions/heartbeat.go : HeartbeatTxnFields"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    hb_address: str = Field(alias="hb-address")
    hb_proof: "HbProofFieldsSchema" = Field(alias="hb-proof")
    hb_seed: str = Field(alias="hb-seed")
    hb_vote_id: str = Field(alias="hb-vote-id")
    hb_key_dilution: int = Field(alias="hb-key-dilution")
