# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import nested, wire

from ._source_map import SourceMap


@dataclass(slots=True)
class CompileResponse:
    hash_: str = field(
        default="",
        metadata=wire("hash"),
    )
    result: str = field(
        default="",
        metadata=wire("result"),
    )
    sourcemap: SourceMap | None = field(
        default=None,
        metadata=nested("sourcemap", lambda: SourceMap),
    )
