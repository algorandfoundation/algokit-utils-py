# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire

from ._serde_helpers import decode_bytes, decode_fixed_bytes, encode_bytes, encode_fixed_bytes


@dataclass(slots=True)
class AssetParams:
    r"""
    AssetParams specifies the parameters for an asset.

    \[apar\] when part of an AssetConfig transaction.

    Definition:
    data/transactions/asset.go : AssetParams
    """

    creator: str = field(
        default="",
        metadata=wire("creator"),
    )
    decimals: int = field(
        default=0,
        metadata=wire("decimals"),
    )
    total: int = field(
        default=0,
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
        metadata=wire(
            "metadata-hash",
            encode=lambda v: encode_fixed_bytes(v, 32),
            decode=lambda raw: decode_fixed_bytes(raw, 32),
        ),
    )
    name: str | None = field(
        default=None,
        metadata=wire("name"),
    )
    name_b64: bytes | None = field(
        default=None,
        metadata=wire(
            "name-b64",
            encode=encode_bytes,
            decode=decode_bytes,
        ),
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
        metadata=wire(
            "unit-name-b64",
            encode=encode_bytes,
            decode=decode_bytes,
        ),
    )
    url: str | None = field(
        default=None,
        metadata=wire("url"),
    )
    url_b64: bytes | None = field(
        default=None,
        metadata=wire(
            "url-b64",
            encode=encode_bytes,
            decode=decode_bytes,
        ),
    )
