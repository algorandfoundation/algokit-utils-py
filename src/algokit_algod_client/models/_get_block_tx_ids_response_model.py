# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class GetBlockTxIdsResponseModel:
    block_tx_ids: list[str] = field(
        metadata=wire("blockTxids"),
    )
