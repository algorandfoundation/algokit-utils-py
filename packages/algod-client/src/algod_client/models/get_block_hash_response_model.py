from __future__ import annotations

from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class GetBlockHashResponseModel:
    block_hash: str = field(
        metadata=wire("blockHash"),
    )
