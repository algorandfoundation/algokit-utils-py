# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class BlockHashResponse:
    block_hash: str = field(
        default="",
        metadata=wire("blockHash"),
    )
