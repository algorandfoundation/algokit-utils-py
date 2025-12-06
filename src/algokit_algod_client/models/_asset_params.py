# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire

from ._serde_helpers import decode_bytes_base64, encode_bytes_base64


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
            encode=encode_bytes_base64,
            decode=decode_bytes_base64,
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
            encode=encode_bytes_base64,
            decode=decode_bytes_base64,
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
            encode=encode_bytes_base64,
            decode=decode_bytes_base64,
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
            encode=encode_bytes_base64,
            decode=decode_bytes_base64,
        ),
    )
