from __future__ import annotations

from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class BuildVersionContainsTheCurrentAlgodBuildVersionInformation:
    branch: str = field(
        metadata=wire("branch"),
    )
    build_number: int = field(
        metadata=wire("build_number"),
    )
    channel: str = field(
        metadata=wire("channel"),
    )
    commit_hash: str = field(
        metadata=wire("commit_hash"),
    )
    major: int = field(
        metadata=wire("major"),
    )
    minor: int = field(
        metadata=wire("minor"),
    )
