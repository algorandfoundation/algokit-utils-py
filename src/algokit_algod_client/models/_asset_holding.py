# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class AssetHolding:
    """
    Describes an asset held by an account.

    Definition:
    data/basics/userBalance.go : AssetHolding
    """

    amount: int = field(
        default=0,
        metadata=wire("amount"),
    )
    asset_id: int = field(
        default=0,
        metadata=wire("asset-id"),
    )
    is_frozen: bool = field(
        default=False,
        metadata=wire("is-frozen"),
    )
