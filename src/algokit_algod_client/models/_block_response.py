# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import nested, wire

from ._block import Block


@dataclass(slots=True)
class BlockResponse:
    block: Block = field(
        metadata=nested("block", lambda: Block),
    )
    cert: dict[str, object] | None = field(
        default=None,
        metadata=wire("cert"),
    )
