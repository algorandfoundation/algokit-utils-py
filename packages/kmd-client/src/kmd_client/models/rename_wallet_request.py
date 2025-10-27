from __future__ import annotations

from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class RenameWalletRequest:
    """
    APIV1POSTWalletRenameRequest is the request for `POST /v1/wallet/rename`
    """

    wallet_id: str | None = field(
        default=None,
        metadata=wire("wallet_id"),
    )
    wallet_name: str | None = field(
        default=None,
        metadata=wire("wallet_name"),
    )
    wallet_password: str | None = field(
        default=None,
        metadata=wire("wallet_password"),
    )
