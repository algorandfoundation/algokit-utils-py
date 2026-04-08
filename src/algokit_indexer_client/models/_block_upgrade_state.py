# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class BlockUpgradeState:
    """
    Fields relating to a protocol upgrade.
    """

    current_protocol: str = field(
        default="",
        metadata=wire("current-protocol"),
    )
    next_protocol: str | None = field(
        default=None,
        metadata=wire("next-protocol"),
    )
    next_protocol_approvals: int | None = field(
        default=None,
        metadata=wire("next-protocol-approvals"),
    )
    next_protocol_switch_on: int | None = field(
        default=None,
        metadata=wire("next-protocol-switch-on"),
    )
    next_protocol_vote_before: int | None = field(
        default=None,
        metadata=wire("next-protocol-vote-before"),
    )
