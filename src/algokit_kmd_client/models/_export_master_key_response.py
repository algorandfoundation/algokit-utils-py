# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire

from ._serde_helpers import decode_bytes, encode_bytes


@dataclass(slots=True)
class ExportMasterKeyResponse:
    """
    ExportMasterKeyResponse is the response to `POST /v1/master-key/export`
    """

    master_derivation_key: bytes = field(
        default=b"",
        metadata=wire(
            "master_derivation_key",
            encode=encode_bytes,
            decode=decode_bytes,
        ),
    )
