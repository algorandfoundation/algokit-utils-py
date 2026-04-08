# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class SourceMap:
    """
    Source map for the program
    """

    mappings: str = field(
        default="",
        metadata=wire("mappings"),
    )
    names: list[str] = field(
        default_factory=list,
        metadata=wire("names"),
    )
    sources: list[str] = field(
        default_factory=list,
        metadata=wire("sources"),
    )
    version: int = field(
        default=0,
        metadata=wire("version"),
    )
