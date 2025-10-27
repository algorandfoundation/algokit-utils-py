from __future__ import annotations

from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class PosttransactionSignResponse:
    """
    APIV1POSTTransactionSignResponse is the response to `POST /v1/transaction/sign`
    friendly:SignTransactionResponse
    """

    error: bool | None = field(
        default=None,
        metadata=wire("error"),
    )
    message: str | None = field(
        default=None,
        metadata=wire("message"),
    )
    signed_transaction: bytes | None = field(
        default=None,
        metadata=wire("signed_transaction"),
    )
