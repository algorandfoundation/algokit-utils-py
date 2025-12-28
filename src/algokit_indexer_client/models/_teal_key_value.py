# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import nested, wire

from ._serde_helpers import decode_bytes, encode_bytes
from ._teal_value import TealValue


@dataclass(slots=True)
class TealKeyValue:
    """
    Represents a key-value pair in an application store.
    """

    value: TealValue = field(
        metadata=nested("value", lambda: TealValue, required=True),
    )
    key: bytes = field(
        default=b"",
        metadata=wire(
            "key",
            encode=encode_bytes,
            decode=decode_bytes,
        ),
    )
