# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import nested, wire

from ._avm_value import AvmValue
from ._serde_helpers import decode_bytes, encode_bytes


@dataclass(slots=True)
class AvmKeyValue:
    """
    Represents an AVM key-value pair in an application store.
    """

    value: AvmValue = field(
        metadata=nested("value", lambda: AvmValue, required=True),
    )
    key: bytes = field(
        default=b"",
        metadata=wire(
            "key",
            encode=encode_bytes,
            decode=decode_bytes,
        ),
    )
