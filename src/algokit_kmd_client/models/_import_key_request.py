# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class ImportKeyRequest:
    """
    APIV1POSTKeyImportRequest is the request for `POST /v1/key/import`
    """

    private_key: bytes | None = field(
        default=None,
        metadata=wire("private_key"),
    )
    wallet_handle_token: str | None = field(
        default=None,
        metadata=wire("wallet_handle_token"),
    )
