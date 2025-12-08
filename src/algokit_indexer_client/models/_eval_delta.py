# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class EvalDelta:
    """
    Represents a TEAL value delta.
    """

    action: int = field(
        default=0,
        metadata=wire("action"),
    )
    bytes_: str | None = field(
        default=None,
        metadata=wire("bytes"),
    )
    uint: int | None = field(
        default=None,
        metadata=wire("uint"),
    )
