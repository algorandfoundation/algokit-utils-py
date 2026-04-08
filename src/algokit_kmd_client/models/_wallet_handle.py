# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import nested, wire

from ._wallet import Wallet


@dataclass(slots=True)
class WalletHandle:
    """
    WalletHandle includes the wallet the handle corresponds to
    and the number of number of seconds to expiration
    """

    wallet: Wallet = field(
        metadata=nested("wallet", lambda: Wallet, required=True),
    )
    expires_seconds: int = field(
        default=0,
        metadata=wire("expires_seconds"),
    )
