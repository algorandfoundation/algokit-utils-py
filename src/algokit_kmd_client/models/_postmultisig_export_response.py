# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class PostmultisigExportResponse:
    """
    APIV1POSTMultisigExportResponse is the response to `POST /v1/multisig/export`
    friendly:ExportMultisigResponse
    """

    error: bool | None = field(
        default=None,
        metadata=wire("error"),
    )
    message: str | None = field(
        default=None,
        metadata=wire("message"),
    )
    multisig_version: int | None = field(
        default=None,
        metadata=wire("multisig_version"),
    )
    pks: list[list[int]] | None = field(
        default=None,
        metadata=wire("pks"),
    )
    threshold: int | None = field(
        default=None,
        metadata=wire("threshold"),
    )
