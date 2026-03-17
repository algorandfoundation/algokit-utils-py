from pydantic import BaseModel, ConfigDict, Field


class TransactionParametersResponseSchema(BaseModel):
    """TransactionParams contains the parameters that help a client construct
    a new transaction."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    consensus_version: str = Field(alias="consensus-version")
    fee: int = Field(alias="fee")
    genesis_hash: str = Field(alias="genesis-hash")
    genesis_id: str = Field(alias="genesis-id")
    last_round: int = Field(alias="last-round")
    min_fee: int = Field(alias="min-fee")
