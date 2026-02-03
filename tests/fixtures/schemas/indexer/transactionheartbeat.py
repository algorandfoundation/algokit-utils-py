from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class TransactionHeartbeatSchema(BaseModel):
    """Fields for a heartbeat transaction.

    Definition:
    data/transactions/heartbeat.go : HeartbeatTxnFields"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    hb_address: str = Field(default=None, alias="hb-address")
    hb_proof: "HbProofFieldsSchema" = Field(default=None, alias="hb-proof")
    hb_seed: str = Field(default=None, alias="hb-seed")
    hb_vote_id: str = Field(default=None, alias="hb-vote-id")
    hb_key_dilution: int = Field(default=None, alias="hb-key-dilution")
