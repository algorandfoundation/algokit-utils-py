# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class NodeStatusResponse:
    """
    NodeStatus contains the information about a node status
    """

    catchup_time: int = field(
        default=0,
        metadata=wire("catchup-time"),
    )
    last_round: int = field(
        default=0,
        metadata=wire("last-round"),
    )
    last_version: str = field(
        default="",
        metadata=wire("last-version"),
    )
    next_version: str = field(
        default="",
        metadata=wire("next-version"),
    )
    next_version_round: int = field(
        default=0,
        metadata=wire("next-version-round"),
    )
    next_version_supported: bool = field(
        default=False,
        metadata=wire("next-version-supported"),
    )
    stopped_at_unsupported_round: bool = field(
        default=False,
        metadata=wire("stopped-at-unsupported-round"),
    )
    time_since_last_round: int = field(
        default=0,
        metadata=wire("time-since-last-round"),
    )
    catchpoint: str | None = field(
        default=None,
        metadata=wire("catchpoint"),
    )
    catchpoint_acquired_blocks: int | None = field(
        default=None,
        metadata=wire("catchpoint-acquired-blocks"),
    )
    catchpoint_processed_accounts: int | None = field(
        default=None,
        metadata=wire("catchpoint-processed-accounts"),
    )
    catchpoint_processed_kvs: int | None = field(
        default=None,
        metadata=wire("catchpoint-processed-kvs"),
    )
    catchpoint_total_accounts: int | None = field(
        default=None,
        metadata=wire("catchpoint-total-accounts"),
    )
    catchpoint_total_blocks: int | None = field(
        default=None,
        metadata=wire("catchpoint-total-blocks"),
    )
    catchpoint_total_kvs: int | None = field(
        default=None,
        metadata=wire("catchpoint-total-kvs"),
    )
    catchpoint_verified_accounts: int | None = field(
        default=None,
        metadata=wire("catchpoint-verified-accounts"),
    )
    catchpoint_verified_kvs: int | None = field(
        default=None,
        metadata=wire("catchpoint-verified-kvs"),
    )
    last_catchpoint: str | None = field(
        default=None,
        metadata=wire("last-catchpoint"),
    )
    upgrade_delay: int | None = field(
        default=None,
        metadata=wire("upgrade-delay"),
    )
    upgrade_next_protocol_vote_before: int | None = field(
        default=None,
        metadata=wire("upgrade-next-protocol-vote-before"),
    )
    upgrade_no_votes: int | None = field(
        default=None,
        metadata=wire("upgrade-no-votes"),
    )
    upgrade_node_vote: bool | None = field(
        default=None,
        metadata=wire("upgrade-node-vote"),
    )
    upgrade_vote_rounds: int | None = field(
        default=None,
        metadata=wire("upgrade-vote-rounds"),
    )
    upgrade_votes: int | None = field(
        default=None,
        metadata=wire("upgrade-votes"),
    )
    upgrade_votes_required: int | None = field(
        default=None,
        metadata=wire("upgrade-votes-required"),
    )
    upgrade_yes_votes: int | None = field(
        default=None,
        metadata=wire("upgrade-yes-votes"),
    )
