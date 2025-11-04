# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import nested, wire

from ._asset_params import AssetParams


@dataclass(slots=True)
class Asset:
    """
    Specifies both the unique identifier and the parameters for an asset
    """

    index: int = field(
        metadata=wire("index"),
    )
    params: AssetParams = field(
        metadata=nested("params", lambda: AssetParams),
    )
    created_at_round: int | None = field(
        default=None,
        metadata=wire("created-at-round"),
    )
    deleted: bool | None = field(
        default=None,
        metadata=wire("deleted"),
    )
    destroyed_at_round: int | None = field(
        default=None,
        metadata=wire("destroyed-at-round"),
    )
