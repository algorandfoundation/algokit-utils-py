# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import nested, wire

from ._build_version_contains_the_current_algod_build_version_information import (
    BuildVersionContainsTheCurrentAlgodBuildVersionInformation,
)
from ._serde_helpers import decode_bytes, encode_bytes


@dataclass(slots=True)
class VersionContainsTheCurrentAlgodVersion:
    """
    algod version information.
    """

    build: BuildVersionContainsTheCurrentAlgodBuildVersionInformation = field(
        metadata=nested("build", lambda: BuildVersionContainsTheCurrentAlgodBuildVersionInformation, required=True),
    )
    genesis_hash_b64: bytes = field(
        default=b"",
        metadata=wire(
            "genesis_hash_b64",
            encode=encode_bytes,
            decode=decode_bytes,
        ),
    )
    genesis_id: str = field(
        default="",
        metadata=wire("genesis_id"),
    )
    versions: list[str] = field(
        default_factory=list,
        metadata=wire("versions"),
    )
