from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class StateProofSignatureSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    falcon_signature: str | None = Field(default=None, alias="falcon-signature")
    merkle_array_index: int | None = Field(default=None, alias="merkle-array-index")
    proof: "MerkleArrayProofSchema | None" = Field(default=None, alias="proof")
    verifying_key: str | None = Field(default=None, alias="verifying-key")
