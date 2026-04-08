# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire

from ._serde_helpers import decode_bytes, encode_bytes


@dataclass(slots=True)
class SignTxnRequest:
    """
    The request for `POST /v1/transaction/sign`
    """

    transaction: bytes = field(
        default=b"",
        metadata=wire(
            "transaction",
            encode=encode_bytes,
            decode=decode_bytes,
        ),
    )
    wallet_handle_token: str = field(
        default="",
        metadata=wire("wallet_handle_token"),
    )
    public_key: bytes | None = field(
        default=None,
        metadata=wire(
            "public_key",
            encode=encode_bytes,
            decode=decode_bytes,
        ),
    )
    wallet_password: str | None = field(
        default=None,
        metadata=wire("wallet_password"),
    )
