# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.constants import ZERO_ADDRESS
from algokit_common.serde import wire


@dataclass(slots=True)
class LocalsRef:
    """
    LocalsRef names a local state by referring to an Address and App it belongs to.
    """

    address: str = field(
        default=ZERO_ADDRESS,
        metadata=wire("address"),
    )
    app: int = field(
        default=0,
        metadata=wire("app"),
    )
