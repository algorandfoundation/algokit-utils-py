from pydantic import BaseModel, ConfigDict, Field


class BlockUpgradeVoteSchema(BaseModel):
    """Fields relating to voting for a protocol upgrade."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    upgrade_approve: bool | None = Field(default=None, alias="upgrade-approve")
    upgrade_delay: int | None = Field(default=None, alias="upgrade-delay")
    upgrade_propose: str | None = Field(default=None, alias="upgrade-propose")
