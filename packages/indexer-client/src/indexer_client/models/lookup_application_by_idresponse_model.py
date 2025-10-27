from __future__ import annotations

from dataclasses import dataclass, field

from algokit_common.serde import nested, wire

from .application import Application


@dataclass(slots=True)
class LookupApplicationByIdresponseModel:
    current_round: int = field(
        metadata=wire("current-round"),
    )
    application: Application | None = field(
        default=None,
        metadata=nested("application", lambda: Application),
    )
