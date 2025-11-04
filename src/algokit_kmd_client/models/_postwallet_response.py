# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import nested, wire

from ._wallet import Wallet


@dataclass(slots=True)
class PostwalletResponse:
    """
    APIV1POSTWalletResponse is the response to `POST /v1/wallet`
    friendly:CreateWalletResponse
    """

    error: bool | None = field(
        default=None,
        metadata=wire("error"),
    )
    message: str | None = field(
        default=None,
        metadata=wire("message"),
    )
    wallet: Wallet | None = field(
        default=None,
        metadata=nested("wallet", lambda: Wallet),
    )
