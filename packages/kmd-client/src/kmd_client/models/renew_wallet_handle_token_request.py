from __future__ import annotations

from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class RenewWalletHandleTokenRequest:
    """
    APIV1POSTWalletRenewRequest is the request for `POST /v1/wallet/renew`
    """

    wallet_handle_token: str | None = field(
        default=None,
        metadata=wire("wallet_handle_token"),
    )
