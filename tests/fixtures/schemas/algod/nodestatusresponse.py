from pydantic import BaseModel, ConfigDict, Field


class NodeStatusResponseSchema(BaseModel):
    """NodeStatus contains the information about a node status"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    catchup_time: int = Field(alias="catchup-time")
    last_round: int = Field(alias="last-round")
    last_version: str = Field(alias="last-version")
    next_version: str = Field(alias="next-version")
    next_version_round: int = Field(alias="next-version-round")
    next_version_supported: bool = Field(alias="next-version-supported")
    stopped_at_unsupported_round: bool = Field(alias="stopped-at-unsupported-round")
    time_since_last_round: int = Field(alias="time-since-last-round")
    last_catchpoint: str | None = Field(default=None, alias="last-catchpoint")
    catchpoint: str | None = Field(default=None, alias="catchpoint")
    catchpoint_total_accounts: int | None = Field(default=None, alias="catchpoint-total-accounts")
    catchpoint_processed_accounts: int | None = Field(default=None, alias="catchpoint-processed-accounts")
    catchpoint_verified_accounts: int | None = Field(default=None, alias="catchpoint-verified-accounts")
    catchpoint_total_kvs: int | None = Field(default=None, alias="catchpoint-total-kvs")
    catchpoint_processed_kvs: int | None = Field(default=None, alias="catchpoint-processed-kvs")
    catchpoint_verified_kvs: int | None = Field(default=None, alias="catchpoint-verified-kvs")
    catchpoint_total_blocks: int | None = Field(default=None, alias="catchpoint-total-blocks")
    catchpoint_acquired_blocks: int | None = Field(default=None, alias="catchpoint-acquired-blocks")
    upgrade_delay: int | None = Field(default=None, alias="upgrade-delay")
    upgrade_node_vote: bool | None = Field(default=None, alias="upgrade-node-vote")
    upgrade_votes_required: int | None = Field(default=None, alias="upgrade-votes-required")
    upgrade_votes: int | None = Field(default=None, alias="upgrade-votes")
    upgrade_yes_votes: int | None = Field(default=None, alias="upgrade-yes-votes")
    upgrade_no_votes: int | None = Field(default=None, alias="upgrade-no-votes")
    upgrade_next_protocol_vote_before: int | None = Field(default=None, alias="upgrade-next-protocol-vote-before")
    upgrade_vote_rounds: int | None = Field(default=None, alias="upgrade-vote-rounds")
