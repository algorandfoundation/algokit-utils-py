# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import nested, wire

from ._source_map import SourceMap


@dataclass(slots=True)
class TealCompileResponseModel:
    hash_: str = field(
        metadata=wire("hash"),
    )
    result: str = field(
        metadata=wire("result"),
    )
    sourcemap: SourceMap | None = field(
        default=None,
        metadata=nested("sourcemap", lambda: SourceMap),
    )
