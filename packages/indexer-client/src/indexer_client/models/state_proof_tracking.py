from __future__ import annotations

from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class StateProofTracking:
    next_round: int | None = field(
        default=None,
        metadata=wire("next-round"),
    )
    online_total_weight: int | None = field(
        default=None,
        metadata=wire("online-total-weight"),
    )
    type_: int | None = field(
        default=None,
        metadata=wire("type"),
    )
    voters_commitment: bytes | None = field(
        default=None,
        metadata=wire("voters-commitment"),
    )
