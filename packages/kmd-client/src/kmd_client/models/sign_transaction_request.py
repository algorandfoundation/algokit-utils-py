from __future__ import annotations

from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class SignTransactionRequest:
    """
    APIV1POSTTransactionSignRequest is the request for `POST /v1/transaction/sign`
    """

    public_key: list[int] | None = field(
        default=None,
        metadata=wire("public_key"),
    )
    transaction: bytes | None = field(
        default=None,
        metadata=wire("transaction"),
    )
    wallet_handle_token: str | None = field(
        default=None,
        metadata=wire("wallet_handle_token"),
    )
    wallet_password: str | None = field(
        default=None,
        metadata=wire("wallet_password"),
    )
