from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class TransactionProofSchema(BaseModel):
    """Proof of transaction in a block."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    proof: str = Field(default=None, alias="proof")
    stibhash: str = Field(default=None, alias="stibhash")
    treedepth: int = Field(default=None, alias="treedepth")
    idx: int = Field(default=None, alias="idx")
    hashtype: str = Field(default=None, alias="hashtype")
