# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import nested, wire

from ._eval_delta import EvalDelta


@dataclass(slots=True)
class EvalDeltaKeyValue:
    """
    Key-value pairs for StateDelta.
    """

    value: EvalDelta = field(
        metadata=nested("value", lambda: EvalDelta, required=True),
    )
    key: str = field(
        default="",
        metadata=wire("key"),
    )
