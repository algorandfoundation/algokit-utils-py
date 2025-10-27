from __future__ import annotations

from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class StateSchema:
    r"""
    Represents a \[apls\] local-state or \[apgs\] global-state schema. These schemas
    determine how much storage may be used in a local-state or global-state for an
    application. The more space used, the larger minimum balance must be maintained in the
    account holding the data.
    """

    num_byte_slice: int = field(
        metadata=wire("num-byte-slice"),
    )
    num_uint: int = field(
        metadata=wire("num-uint"),
    )
