# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.constants import ZERO_ADDRESS
from algokit_common.serde import wire


@dataclass(slots=True)
class ApplicationLocalReference:
    """
    References an account's local state for an application.
    """

    account: str = field(
        default=ZERO_ADDRESS,
        metadata=wire("account"),
    )
    app: int = field(
        default=0,
        metadata=wire("app"),
    )
