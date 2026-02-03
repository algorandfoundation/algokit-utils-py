from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class IndexerStateProofMessageSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    block_headers_commitment: str | None = Field(default=None, alias="block-headers-commitment")
    voters_commitment: str | None = Field(default=None, alias="voters-commitment")
    ln_proven_weight: int | None = Field(default=None, alias="ln-proven-weight")
    first_attested_round: int | None = Field(default=None, alias="first-attested-round")
    latest_attested_round: int | None = Field(default=None, alias="latest-attested-round")
