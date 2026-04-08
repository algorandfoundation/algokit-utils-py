# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire

from ._serde_helpers import decode_bytes, encode_bytes


@dataclass(slots=True)
class SignTransactionResponse:
    """
    SignTransactionResponse is the response to `POST /v1/transaction/sign`
    """

    signed_transaction: bytes = field(
        default=b"",
        metadata=wire(
            "signed_transaction",
            encode=encode_bytes,
            decode=decode_bytes,
        ),
    )
