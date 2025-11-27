# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class AvmValue:
    """
    Represents an AVM value.
    """

    type_: int = field(
        default=0,
        metadata=wire("type"),
    )
    bytes_: str | None = field(
        default=None,
        metadata=wire("bytes"),
    )
    uint: int | None = field(
        default=None,
        metadata=wire("uint"),
    )
