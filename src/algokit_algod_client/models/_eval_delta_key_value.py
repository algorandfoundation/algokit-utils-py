# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import nested, wire

from ._eval_delta import EvalDelta
from ._serde_helpers import decode_bytes_base64, encode_bytes_base64


@dataclass(slots=True)
class EvalDeltaKeyValue:
    """
    Key-value pairs for StateDelta.
    """

    key: bytes = field(
        metadata=wire(
            "key",
            encode=encode_bytes_base64,
            decode=decode_bytes_base64,
        ),
    )
    value: EvalDelta = field(
        metadata=nested("value", lambda: EvalDelta),
    )
