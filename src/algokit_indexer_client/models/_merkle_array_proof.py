# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import nested, wire

from ._hash_factory import HashFactory
from ._serde_helpers import decode_bytes_sequence, encode_bytes_sequence


@dataclass(slots=True)
class MerkleArrayProof:
    hash_factory: HashFactory | None = field(
        default=None,
        metadata=nested("hash-factory", lambda: HashFactory),
    )
    path: list[bytes] | None = field(
        default=None,
        metadata=wire(
            "path",
            encode=encode_bytes_sequence,
            decode=decode_bytes_sequence,
        ),
    )
    tree_depth: int | None = field(
        default=None,
        metadata=wire("tree-depth"),
    )
