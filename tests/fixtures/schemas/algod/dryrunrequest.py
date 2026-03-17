from pydantic import BaseModel, ConfigDict, Field


class DryrunRequestSchema(BaseModel):
    """Request data type for dryrun endpoint. Given the Transactions and simulated ledger state upload, run TEAL scripts and return debugging information."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    txns: list[str] = Field(alias="txns")
    accounts: "list[AccountSchema]" = Field(alias="accounts")
    apps: "list[ApplicationSchema]" = Field(alias="apps")
    protocol_version: str = Field(alias="protocol-version")
    round: int = Field(alias="round")
    latest_timestamp: int = Field(ge=0, alias="latest-timestamp")
    sources: "list[DryrunSourceSchema]" = Field(alias="sources")
