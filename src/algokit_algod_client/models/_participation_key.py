# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import nested, wire

from ._account_participation import AccountParticipation


@dataclass(slots=True)
class ParticipationKey:
    """
    Represents a participation key used by the node.
    """

    address: str = field(
        metadata=wire("address"),
    )
    id_: str = field(
        metadata=wire("id"),
    )
    key: AccountParticipation = field(
        metadata=nested("key", lambda: AccountParticipation),
    )
    effective_first_valid: int | None = field(
        default=None,
        metadata=wire("effective-first-valid"),
    )
    effective_last_valid: int | None = field(
        default=None,
        metadata=wire("effective-last-valid"),
    )
    last_block_proposal: int | None = field(
        default=None,
        metadata=wire("last-block-proposal"),
    )
    last_state_proof: int | None = field(
        default=None,
        metadata=wire("last-state-proof"),
    )
    last_vote: int | None = field(
        default=None,
        metadata=wire("last-vote"),
    )
