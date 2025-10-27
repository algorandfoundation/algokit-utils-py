from __future__ import annotations

from dataclasses import dataclass, field

from algokit_common.serde import nested, wire

from .allocations_for_genesis_file_state_model import AllocationsForGenesisFileStateModel


@dataclass(slots=True)
class AllocationsForGenesisFile:
    addr: str = field(
        metadata=wire("addr"),
    )
    comment: str = field(
        metadata=wire("comment"),
    )
    state: AllocationsForGenesisFileStateModel = field(
        metadata=nested("state", lambda: AllocationsForGenesisFileStateModel),
    )
