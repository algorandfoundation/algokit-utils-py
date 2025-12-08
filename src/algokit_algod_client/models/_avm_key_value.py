# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import nested, wire

from ._avm_value import AvmValue
from ._serde_helpers import decode_bytes_base64, encode_bytes_base64


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
            encode=encode_bytes_base64,
            decode=decode_bytes_base64,
        ),
    )
