from dataclasses import dataclass, field

from algokit_transact.codec.serde import addr, wire


@dataclass(slots=True, frozen=True)
class AssetConfigTransactionFields:
    asset_id: int = field(default=0, metadata=wire("caid"))
    total: int | None = field(default=None, metadata=wire("apar.t"))
    decimals: int | None = field(default=None, metadata=wire("apar.dc"))
    default_frozen: bool | None = field(default=None, metadata=wire("apar.df"))
    unit_name: str | None = field(default=None, metadata=wire("apar.un"))
    asset_name: str | None = field(default=None, metadata=wire("apar.an"))
    url: str | None = field(default=None, metadata=wire("apar.au"))
    metadata_hash: bytes | None = field(default=None, metadata=wire("apar.am"))
    manager: str | None = field(default=None, metadata=addr("apar.m", omit_if_none=True))
    reserve: str | None = field(default=None, metadata=addr("apar.r", omit_if_none=True))
    freeze: str | None = field(default=None, metadata=addr("apar.f", omit_if_none=True))
    clawback: str | None = field(default=None, metadata=addr("apar.c", omit_if_none=True))
