from __future__ import annotations

from dataclasses import dataclass, field

from algokit_common.serde import nested, wire

from .teal_value import TealValue


@dataclass(slots=True)
class TealKeyValue:
    """
    Represents a key-value pair in an application store.
    """

    key: str = field(
        metadata=wire("key"),
    )
    value: TealValue = field(
        metadata=nested("value", lambda: TealValue),
    )
