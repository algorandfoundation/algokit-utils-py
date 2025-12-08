# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire

from ._serde_helpers import decode_model_sequence, encode_model_sequence
from ._wallet import Wallet


@dataclass(slots=True)
class ListWalletsResponse:
    """
    ListWalletsResponse is the response to `GET /v1/wallets`
    """

    wallets: list[Wallet] = field(
        default_factory=list,
        metadata=wire(
            "wallets",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: Wallet, raw),
        ),
    )
