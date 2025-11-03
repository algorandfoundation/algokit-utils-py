# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class TealValue:
    """
    Represents a TEAL value.
    """

    bytes: bytes = field(
        metadata=wire("bytes"),
    )
    type_: int = field(
        metadata=wire("type"),
    )
    uint: int = field(
        metadata=wire("uint"),
    )
