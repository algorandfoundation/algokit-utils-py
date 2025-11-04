# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class AssetParams:
    r"""
    AssetParams specifies the parameters for an asset.

    \[apar\] when part of an AssetConfig transaction.

    Definition:
    data/transactions/asset.go : AssetParams
    """

    creator: str = field(
        metadata=wire("creator"),
    )
    decimals: int = field(
        metadata=wire("decimals"),
    )
    total: int = field(
        metadata=wire("total"),
    )
    clawback: str | None = field(
        default=None,
        metadata=wire("clawback"),
    )
    default_frozen: bool | None = field(
        default=None,
        metadata=wire("default-frozen"),
    )
    freeze: str | None = field(
        default=None,
        metadata=wire("freeze"),
    )
    manager: str | None = field(
        default=None,
        metadata=wire("manager"),
    )
    metadata_hash: bytes | None = field(
        default=None,
        metadata=wire("metadata-hash"),
    )
    name: str | None = field(
        default=None,
        metadata=wire("name"),
    )
    name_b64: bytes | None = field(
        default=None,
        metadata=wire("name-b64"),
    )
    reserve: str | None = field(
        default=None,
        metadata=wire("reserve"),
    )
    unit_name: str | None = field(
        default=None,
        metadata=wire("unit-name"),
    )
    unit_name_b64: bytes | None = field(
        default=None,
        metadata=wire("unit-name-b64"),
    )
    url: str | None = field(
        default=None,
        metadata=wire("url"),
    )
    url_b64: bytes | None = field(
        default=None,
        metadata=wire("url-b64"),
    )
