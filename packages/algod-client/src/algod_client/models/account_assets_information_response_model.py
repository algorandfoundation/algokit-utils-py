from __future__ import annotations

from dataclasses import dataclass, field

from algokit_common.serde import wire

from ._serde_helpers import decode_model_sequence, encode_model_sequence
from .account_asset_holding import AccountAssetHolding


@dataclass(slots=True)
class AccountAssetsInformationResponseModel:
    round_: int = field(
        metadata=wire("round"),
    )
    asset_holdings: list[AccountAssetHolding] | None = field(
        default=None,
        metadata=wire(
            "asset-holdings",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: AccountAssetHolding, raw),
        ),
    )
    next_token: str | None = field(
        default=None,
        metadata=wire("next-token"),
    )
