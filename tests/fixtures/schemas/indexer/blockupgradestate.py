from pydantic import BaseModel, ConfigDict, Field


class BlockUpgradeStateSchema(BaseModel):
    """Fields relating to a protocol upgrade."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    current_protocol: str = Field(alias="current-protocol")
    next_protocol: str | None = Field(default=None, alias="next-protocol")
    next_protocol_approvals: int | None = Field(default=None, alias="next-protocol-approvals")
    next_protocol_switch_on: int | None = Field(default=None, alias="next-protocol-switch-on")
    next_protocol_vote_before: int | None = Field(default=None, alias="next-protocol-vote-before")
