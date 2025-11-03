"""Shared serialization helpers for AlgoKit dataclasses.

The implementation mirrors the serde utilities that previously lived in
``algokit_transact`` so that auto-generated API clients can share the same
wire-format logic.
"""

from algokit_common.serde._core import (
    DecodeError,
    EncodeError,
    addr,
    addr_seq,
    bytes_seq,
    enum_value,
    flatten,
    from_wire,
    int_seq,
    nested,
    sort_msgpack_value,
    to_wire,
    to_wire_canonical,
    wire,
)

__all__ = [
    "DecodeError",
    "EncodeError",
    "addr",
    "addr_seq",
    "bytes_seq",
    "enum_value",
    "flatten",
    "from_wire",
    "int_seq",
    "nested",
    "sort_msgpack_value",
    "to_wire",
    "to_wire_canonical",
    "wire",
]
