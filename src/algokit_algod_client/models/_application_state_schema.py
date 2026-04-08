# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class ApplicationStateSchema:
    """
    Specifies maximums on the number of each type that may be stored.
    """

    num_byte_slices: int = field(
        default=0,
        metadata=wire("num-byte-slice"),
    )
    num_uints: int = field(
        default=0,
        metadata=wire("num-uint"),
    )
