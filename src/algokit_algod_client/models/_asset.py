# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import nested, wire

from ._asset_params import AssetParams


@dataclass(slots=True)
class Asset:
    """
    Specifies both the unique identifier and the parameters for an asset
    """

    id_: int = field(
        metadata=wire("id"),
    )
    params: AssetParams = field(
        metadata=nested("params", lambda: AssetParams),
    )
