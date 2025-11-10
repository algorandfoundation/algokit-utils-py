# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire

from ._serde_helpers import decode_bytes_base64, encode_bytes_base64


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
        metadata=wire(
            "signed_transaction",
            encode=encode_bytes_base64,
            decode=decode_bytes_base64,
        ),
    )
