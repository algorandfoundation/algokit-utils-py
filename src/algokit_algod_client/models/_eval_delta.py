# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class EvalDelta:
    """
    Represents a TEAL value delta.
    """

    action: int = field(
        metadata=wire("action"),
    )
    bytes: str | None = field(
        default=None,
        metadata=wire("bytes"),
    )
    uint: int | None = field(
        default=None,
        metadata=wire("uint"),
    )
