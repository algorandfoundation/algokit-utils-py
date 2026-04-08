# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import nested, wire

from ._avm_value import AvmValue


@dataclass(slots=True)
class ScratchChange:
    """
    A write operation into a scratch slot.
    """

    new_value: AvmValue = field(
        metadata=nested("new-value", lambda: AvmValue, required=True),
    )
    slot: int = field(
        default=0,
        metadata=wire("slot"),
    )
