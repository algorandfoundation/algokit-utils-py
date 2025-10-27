from __future__ import annotations

from dataclasses import dataclass, field

from algokit_common.serde import wire

from ._serde_helpers import decode_model_sequence, encode_model_sequence
from .wallet import Wallet


@dataclass(slots=True)
class GetwalletsResponse:
    """
    APIV1GETWalletsResponse is the response to `GET /v1/wallets`
    friendly:ListWalletsResponse
    """

    error: bool | None = field(
        default=None,
        metadata=wire("error"),
    )
    message: str | None = field(
        default=None,
        metadata=wire("message"),
    )
    wallets: list[Wallet] | None = field(
        default=None,
        metadata=wire(
            "wallets",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: Wallet, raw),
        ),
    )
