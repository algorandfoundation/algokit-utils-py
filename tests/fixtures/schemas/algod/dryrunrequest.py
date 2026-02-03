from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class DryrunRequestSchema(BaseModel):
    """Request data type for dryrun endpoint. Given the Transactions and simulated ledger state upload, run TEAL scripts and return debugging information."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    txns: list[str] = Field(default=None, alias="txns")
    accounts: "list[AccountSchema]" = Field(default=None, alias="accounts")
    apps: "list[ApplicationSchema]" = Field(default=None, alias="apps")
    protocol_version: str = Field(default=None, alias="protocol-version")
    round: int = Field(default=None, alias="round")
    latest_timestamp: int = Field(default=None, ge=0, alias="latest-timestamp")
    sources: "list[DryrunSourceSchema]" = Field(default=None, alias="sources")
