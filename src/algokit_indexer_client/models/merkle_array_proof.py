# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import nested, wire

from .hash_factory import HashFactory


@dataclass(slots=True)
class MerkleArrayProof:
    hash_factory: HashFactory | None = field(
        default=None,
        metadata=nested("hash-factory", lambda: HashFactory),
    )
    path: list[bytes] | None = field(
        default=None,
        metadata=wire("path"),
    )
    tree_depth: int | None = field(
        default=None,
        metadata=wire("tree-depth"),
    )
