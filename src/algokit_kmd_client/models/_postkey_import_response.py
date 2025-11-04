# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class PostkeyImportResponse:
    """
    APIV1POSTKeyImportResponse is the response to `POST /v1/key/import`
    friendly:ImportKeyResponse
    """

    address: str | None = field(
        default=None,
        metadata=wire("address"),
    )
    error: bool | None = field(
        default=None,
        metadata=wire("error"),
    )
    message: str | None = field(
        default=None,
        metadata=wire("message"),
    )
