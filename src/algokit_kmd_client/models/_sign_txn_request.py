# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire

from ._serde_helpers import decode_bytes_base64, encode_bytes_base64


@dataclass(slots=True)
class SignTxnRequest:
    """
    The request for `POST /v1/transaction/sign`
    """

    transaction: bytes = field(
        default=b"",
        metadata=wire(
            "transaction",
            encode=encode_bytes_base64,
            decode=decode_bytes_base64,
        ),
    )
    wallet_handle_token: str = field(
        default="",
        metadata=wire("wallet_handle_token"),
    )
    public_key: list[int] | None = field(
        default=None,
        metadata=wire("public_key"),
    )
    wallet_password: str | None = field(
        default=None,
        metadata=wire("wallet_password"),
    )
