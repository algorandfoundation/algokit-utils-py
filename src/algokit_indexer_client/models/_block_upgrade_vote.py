# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class BlockUpgradeVote:
    """
    Fields relating to voting for a protocol upgrade.
    """

    upgrade_approve: bool | None = field(
        default=None,
        metadata=wire("upgrade-approve"),
    )
    upgrade_delay: int | None = field(
        default=None,
        metadata=wire("upgrade-delay"),
    )
    upgrade_propose: str | None = field(
        default=None,
        metadata=wire("upgrade-propose"),
    )
