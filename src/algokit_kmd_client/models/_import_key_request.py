# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire

from ._serde_helpers import decode_bytes_base64, encode_bytes_base64


@dataclass(slots=True)
class ImportKeyRequest:
    """
    APIV1POSTKeyImportRequest is the request for `POST /v1/key/import`
    """

    private_key: bytes | None = field(
        default=None,
        metadata=wire(
            "private_key",
            encode=encode_bytes_base64,
            decode=decode_bytes_base64,
        ),
    )
    wallet_handle_token: str | None = field(
        default=None,
        metadata=wire("wallet_handle_token"),
    )
