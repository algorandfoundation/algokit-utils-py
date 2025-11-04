# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class PostkeyExportResponse:
    """
    APIV1POSTKeyExportResponse is the response to `POST /v1/key/export`
    friendly:ExportKeyResponse
    """

    error: bool | None = field(
        default=None,
        metadata=wire("error"),
    )
    message: str | None = field(
        default=None,
        metadata=wire("message"),
    )
    private_key: bytes | None = field(
        default=None,
        metadata=wire("private_key"),
    )
