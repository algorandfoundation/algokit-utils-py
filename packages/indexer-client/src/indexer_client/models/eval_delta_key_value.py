from __future__ import annotations

from dataclasses import dataclass, field

from algokit_common.serde import nested, wire

from .eval_delta import EvalDelta


@dataclass(slots=True)
class EvalDeltaKeyValue:
    """
    Key-value pairs for StateDelta.
    """

    key: str = field(
        metadata=wire("key"),
    )
    value: EvalDelta = field(
        metadata=nested("value", lambda: EvalDelta),
    )
