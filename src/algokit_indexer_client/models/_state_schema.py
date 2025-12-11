# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class StateSchema:
    r"""
    Represents a \[apls\] local-state or \[apgs\] global-state schema. These schemas
    determine how much storage may be used in a local-state or global-state for an
    application. The more space used, the larger minimum balance must be maintained in the
    account holding the data.
    """

    num_byte_slices: int = field(
        default=0,
        metadata=wire("num-byte-slice"),
    )
    num_uints: int = field(
        default=0,
        metadata=wire("num-uint"),
    )
