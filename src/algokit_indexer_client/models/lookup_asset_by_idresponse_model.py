# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import nested, wire

from .asset import Asset


@dataclass(slots=True)
class LookupAssetByIdresponseModel:
    asset: Asset = field(
        metadata=nested("asset", lambda: Asset),
    )
    current_round: int = field(
        metadata=wire("current-round"),
    )
