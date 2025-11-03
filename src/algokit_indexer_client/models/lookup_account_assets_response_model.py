# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire

from ._serde_helpers import decode_model_sequence, encode_model_sequence
from .asset_holding import AssetHolding


@dataclass(slots=True)
class LookupAccountAssetsResponseModel:
    assets: list[AssetHolding] = field(
        metadata=wire(
            "assets",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: AssetHolding, raw),
        ),
    )
    current_round: int = field(
        metadata=wire("current-round"),
    )
    next_token: str | None = field(
        default=None,
        metadata=wire("next-token"),
    )
