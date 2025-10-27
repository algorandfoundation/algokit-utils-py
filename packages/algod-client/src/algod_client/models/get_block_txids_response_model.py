from __future__ import annotations

from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class GetBlockTxidsResponseModel:
    block_txids: list[str] = field(
        metadata=wire("blockTxids"),
    )
