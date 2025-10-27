from __future__ import annotations

from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class ApplicationStateSchema:
    """
    Specifies maximums on the number of each type that may be stored.
    """

    num_byte_slice: int = field(
        metadata=wire("num-byte-slice"),
    )
    num_uint: int = field(
        metadata=wire("num-uint"),
    )
