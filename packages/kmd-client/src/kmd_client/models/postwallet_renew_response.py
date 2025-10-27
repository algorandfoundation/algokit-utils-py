from __future__ import annotations

from dataclasses import dataclass, field

from algokit_common.serde import nested, wire

from .wallet_handle import WalletHandle


@dataclass(slots=True)
class PostwalletRenewResponse:
    """
    APIV1POSTWalletRenewResponse is the response to `POST /v1/wallet/renew`
    friendly:RenewWalletHandleTokenResponse
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
