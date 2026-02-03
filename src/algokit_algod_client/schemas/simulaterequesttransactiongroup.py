from pydantic import BaseModel, ConfigDict, Field


class SimulateRequestTransactionGroupSchema(BaseModel):
    """A transaction group to simulate."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    txns: list[str] = Field(default=None, alias="txns")
