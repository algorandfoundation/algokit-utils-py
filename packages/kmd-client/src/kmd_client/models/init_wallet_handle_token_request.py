from __future__ import annotations

from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class InitWalletHandleTokenRequest:
    """
    APIV1POSTWalletInitRequest is the request for `POST /v1/wallet/init`
    """

    wallet_id: str | None = field(
        default=None,
        metadata=wire("wallet_id"),
    )
    wallet_password: str | None = field(
        default=None,
        metadata=wire("wallet_password"),
    )
