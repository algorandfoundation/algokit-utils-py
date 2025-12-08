# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import nested, wire

from ._allocations_for_genesis_file_state_model import AllocationsForGenesisFileStateModel


@dataclass(slots=True)
class AllocationsForGenesisFile:
    state: AllocationsForGenesisFileStateModel = field(
        metadata=nested("state", lambda: AllocationsForGenesisFileStateModel, required=True),
    )
    addr: str = field(
        default="",
        metadata=wire("addr"),
    )
    comment: str = field(
        default="",
        metadata=wire("comment"),
    )
