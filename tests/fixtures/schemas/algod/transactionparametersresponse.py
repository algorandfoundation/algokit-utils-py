from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class TransactionParametersResponseSchema(BaseModel):
    """TransactionParams contains the parameters that help a client construct
    a new transaction."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    consensus_version: str = Field(default=None, alias="consensus-version")
    fee: int = Field(default=None, alias="fee")
    genesis_hash: str = Field(default=None, alias="genesis-hash")
    genesis_id: str = Field(default=None, alias="genesis-id")
    last_round: int = Field(default=None, alias="last-round")
    min_fee: int = Field(default=None, alias="min-fee")
