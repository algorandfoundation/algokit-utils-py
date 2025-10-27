from __future__ import annotations

from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class ParticipationUpdates:
    """
    Participation account data that needs to be checked/acted on by the network.
    """

    absent_participation_accounts: list[str] | None = field(
        default=None,
        metadata=wire("absent-participation-accounts"),
    )
    expired_participation_accounts: list[str] | None = field(
        default=None,
        metadata=wire("expired-participation-accounts"),
    )
