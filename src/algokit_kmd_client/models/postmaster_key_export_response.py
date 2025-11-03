# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class PostmasterKeyExportResponse:
    """
    APIV1POSTMasterKeyExportResponse is the response to `POST /v1/master-key/export`
    friendly:ExportMasterKeyResponse
    """

    error: bool | None = field(
        default=None,
        metadata=wire("error"),
    )
    master_derivation_key: list[int] | None = field(
        default=None,
        metadata=wire("master_derivation_key"),
    )
    message: str | None = field(
        default=None,
        metadata=wire("message"),
    )
