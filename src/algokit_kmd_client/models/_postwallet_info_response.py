# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import nested, wire

from ._wallet_handle import WalletHandle


@dataclass(slots=True)
class PostwalletInfoResponse:
    """
    APIV1POSTWalletInfoResponse is the response to `POST /v1/wallet/info`
    friendly:WalletInfoResponse
    """

    error: bool | None = field(
        default=None,
        metadata=wire("error"),
    )
    message: str | None = field(
        default=None,
        metadata=wire("message"),
    )
    wallet_handle: WalletHandle | None = field(
        default=None,
        metadata=nested("wallet_handle", lambda: WalletHandle),
    )
