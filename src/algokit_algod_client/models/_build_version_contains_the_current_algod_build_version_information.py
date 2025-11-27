# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class BuildVersionContainsTheCurrentAlgodBuildVersionInformation:
    branch: str = field(
        default="",
        metadata=wire("branch"),
    )
    build_number: int = field(
        default=0,
        metadata=wire("build_number"),
    )
    channel: str = field(
        default="",
        metadata=wire("channel"),
    )
    commit_hash: str = field(
        default="",
        metadata=wire("commit_hash"),
    )
    major: int = field(
        default=0,
        metadata=wire("major"),
    )
    minor: int = field(
        default=0,
        metadata=wire("minor"),
    )
