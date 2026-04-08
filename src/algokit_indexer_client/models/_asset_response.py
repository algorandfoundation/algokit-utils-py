# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import nested, wire

from ._asset import Asset


@dataclass(slots=True)
class AssetResponse:
    asset: Asset = field(
        metadata=nested("asset", lambda: Asset, required=True),
    )
    current_round: int = field(
        default=0,
        metadata=wire("current-round"),
    )
