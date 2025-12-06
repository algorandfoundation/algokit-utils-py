# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire

from ._asset import Asset
from ._serde_helpers import decode_model_sequence, encode_model_sequence


@dataclass(slots=True)
class AssetsResponse:
    assets: list[Asset] = field(
        default_factory=list,
        metadata=wire(
            "assets",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: Asset, raw),
        ),
    )
    current_round: int = field(
        default=0,
        metadata=wire("current-round"),
    )
    next_token: str | None = field(
        default=None,
        metadata=wire("next-token"),
    )
