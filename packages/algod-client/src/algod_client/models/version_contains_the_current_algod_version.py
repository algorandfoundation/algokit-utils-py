from __future__ import annotations

from dataclasses import dataclass, field

from algokit_common.serde import nested, wire

from .build_version_contains_the_current_algod_build_version_information import (
    BuildVersionContainsTheCurrentAlgodBuildVersionInformation,
)


@dataclass(slots=True)
class VersionContainsTheCurrentAlgodVersion:
    """
    algod version information.
    """

    build: BuildVersionContainsTheCurrentAlgodBuildVersionInformation = field(
        metadata=nested("build", lambda: BuildVersionContainsTheCurrentAlgodBuildVersionInformation),
    )
    genesis_hash_b64: bytes = field(
        metadata=wire("genesis_hash_b64"),
    )
    genesis_id: str = field(
        metadata=wire("genesis_id"),
    )
    versions: list[str] = field(
        metadata=wire("versions"),
    )
