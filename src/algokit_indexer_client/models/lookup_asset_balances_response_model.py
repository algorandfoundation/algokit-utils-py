# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire

from ._serde_helpers import decode_model_sequence, encode_model_sequence
from .mini_asset_holding import MiniAssetHolding


@dataclass(slots=True)
class LookupAssetBalancesResponseModel:
    balances: list[MiniAssetHolding] = field(
        metadata=wire(
            "balances",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: MiniAssetHolding, raw),
        ),
    )
    current_round: int = field(
        metadata=wire("current-round"),
    )
    next_token: str | None = field(
        default=None,
        metadata=wire("next-token"),
    )
