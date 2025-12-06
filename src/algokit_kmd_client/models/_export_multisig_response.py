# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class ExportMultisigResponse:
    """
    ExportMultisigResponse is the response to `POST /v1/multisig/export`
    """

    multisig_version: int = field(
        default=0,
        metadata=wire("multisig_version"),
    )
    public_keys: list[list[int]] = field(
        default_factory=list,
        metadata=wire("pks"),
    )
    threshold: int = field(
        default=0,
        metadata=wire("threshold"),
    )
