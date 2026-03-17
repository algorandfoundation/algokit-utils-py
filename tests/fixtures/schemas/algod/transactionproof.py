from pydantic import BaseModel, ConfigDict, Field


class TransactionProofSchema(BaseModel):
    """Proof of transaction in a block."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    proof: str = Field(alias="proof")
    stibhash: str = Field(alias="stibhash")
    treedepth: int = Field(alias="treedepth")
    idx: int = Field(alias="idx")
    hashtype: str = Field(alias="hashtype")
