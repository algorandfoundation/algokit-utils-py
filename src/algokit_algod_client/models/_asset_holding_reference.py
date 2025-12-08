# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.constants import ZERO_ADDRESS
from algokit_common.serde import wire


@dataclass(slots=True)
class AssetHoldingReference:
    """
    References an asset held by an account.
    """

    account: str = field(
        default=ZERO_ADDRESS,
        metadata=wire("account"),
    )
    asset: int = field(
        default=0,
        metadata=wire("asset"),
    )
