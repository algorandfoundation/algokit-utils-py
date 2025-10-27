from __future__ import annotations

from dataclasses import dataclass, field

from algokit_common.serde import nested, wire

from .avm_value import AvmValue


@dataclass(slots=True)
class AvmKeyValue:
    """
    Represents an AVM key-value pair in an application store.
    """

    key: bytes = field(
        metadata=wire("key"),
    )
    value: AvmValue = field(
        metadata=nested("value", lambda: AvmValue),
    )
