# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire

from ._mini_asset_holding import MiniAssetHolding
from ._serde_helpers import decode_model_sequence, encode_model_sequence


@dataclass(slots=True)
class AssetBalancesResponse:
    balances: list[MiniAssetHolding] = field(
        default_factory=list,
        metadata=wire(
            "balances",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: MiniAssetHolding, raw),
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
