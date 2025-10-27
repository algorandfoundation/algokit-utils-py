from __future__ import annotations

from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class Wallet:
    """
    APIV1Wallet is the API's representation of a wallet
    """

    driver_name: str | None = field(
        default=None,
        metadata=wire("driver_name"),
    )
    driver_version: int | None = field(
        default=None,
        metadata=wire("driver_version"),
    )
    id_: str | None = field(
        default=None,
        metadata=wire("id"),
    )
    mnemonic_ux: bool | None = field(
        default=None,
        metadata=wire("mnemonic_ux"),
    )
    name: str | None = field(
        default=None,
        metadata=wire("name"),
    )
    supported_txs: list[str] | None = field(
        default=None,
        metadata=wire("supported_txs"),
    )
