# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class BlockTxidsResponse:
    block_tx_ids: list[str] = field(
        default_factory=list,
        metadata=wire("blockTxids"),
    )
