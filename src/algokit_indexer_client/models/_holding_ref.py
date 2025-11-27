# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.constants import ZERO_ADDRESS
from algokit_common.serde import wire


@dataclass(slots=True)
class HoldingRef:
    """
    HoldingRef names a holding by referring to an Address and Asset it belongs to.
    """

    address: str = field(
        default=ZERO_ADDRESS,
        metadata=wire("address"),
    )
    asset: int = field(
        default=0,
        metadata=wire("asset"),
    )
