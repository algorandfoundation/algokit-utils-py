# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import nested, wire

from ._avm_value import AvmValue
from ._serde_helpers import decode_bytes, encode_bytes


@dataclass(slots=True)
class ApplicationStateOperation:
    """
    An operation against an application's global/local/box state.
    """

    app_state_type: str = field(
        default="",
        metadata=wire("app-state-type"),
    )
    key: bytes = field(
        default=b"",
        metadata=wire(
            "key",
            encode=encode_bytes,
            decode=decode_bytes,
        ),
    )
    operation: str = field(
        default="",
        metadata=wire("operation"),
    )
    account: str | None = field(
        default=None,
        metadata=wire("account"),
    )
    new_value: AvmValue | None = field(
        default=None,
        metadata=nested("new-value", lambda: AvmValue),
    )
