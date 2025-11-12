# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class SourceMap:
    """
    Source map for the program
    """

    mappings: str = field(
        metadata=wire("mappings"),
    )
    names: list[str] = field(
        metadata=wire("names"),
    )
    sources: list[str] = field(
        metadata=wire("sources"),
    )
    version: int = field(
        metadata=wire("version"),
    )
