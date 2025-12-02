# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class ExportMasterKeyResponse:
    """
    ExportMasterKeyResponse is the response to `POST /v1/master-key/export`
    """

    master_derivation_key: list[int] = field(
        default_factory=list,
        metadata=wire("master_derivation_key"),
    )
