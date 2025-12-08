# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class Wallet:
    """
    Wallet is the API's representation of a wallet
    """

    driver_name: str = field(
        default="",
        metadata=wire("driver_name"),
    )
    driver_version: int = field(
        default=0,
        metadata=wire("driver_version"),
    )
    id_: str = field(
        default="",
        metadata=wire("id"),
    )
    mnemonic_ux: bool = field(
        default=False,
        metadata=wire("mnemonic_ux"),
    )
    name: str = field(
        default="",
        metadata=wire("name"),
    )
    supported_txs: list[str] = field(
        default_factory=list,
        metadata=wire("supported_txs"),
    )
