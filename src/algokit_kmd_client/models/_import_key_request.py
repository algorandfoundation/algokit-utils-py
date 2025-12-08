# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire

from ._serde_helpers import decode_bytes_base64, encode_bytes_base64


@dataclass(slots=True)
class ImportKeyRequest:
    """
    The request for `POST /v1/key/import`
    """

    private_key: bytes = field(
        default=b"",
        metadata=wire(
            "private_key",
            encode=encode_bytes_base64,
            decode=decode_bytes_base64,
        ),
    )
    wallet_handle_token: str = field(
        default="",
        metadata=wire("wallet_handle_token"),
    )
