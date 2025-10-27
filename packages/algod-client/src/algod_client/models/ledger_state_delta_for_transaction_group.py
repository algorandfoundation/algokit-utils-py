from __future__ import annotations

from dataclasses import dataclass, field

from algokit_common.serde import nested, wire

from .ledger_state_delta import LedgerStateDelta


@dataclass(slots=True)
class LedgerStateDeltaForTransactionGroup:
    """
    Contains a ledger delta for a single transaction group
    """

    delta: LedgerStateDelta = field(
        metadata=nested("Delta", lambda: LedgerStateDelta),
    )
    ids: list[str] = field(
        metadata=wire("Ids"),
    )
