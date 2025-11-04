# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire

from ._block import Block
from ._serde_helpers import decode_model_sequence, encode_model_sequence


@dataclass(slots=True)
class SearchForBlockHeadersResponseModel:
    blocks: list[Block] = field(
        metadata=wire(
            "blocks",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: Block, raw),
        ),
    )
    current_round: int = field(
        metadata=wire("current-round"),
    )
    next_token: str | None = field(
        default=None,
        metadata=wire("next-token"),
    )
