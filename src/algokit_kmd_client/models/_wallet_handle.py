# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import nested, wire

from ._wallet import Wallet


@dataclass(slots=True)
class WalletHandle:
    """
    APIV1WalletHandle includes the wallet the handle corresponds to
    and the number of number of seconds to expiration
    """

    expires_seconds: int | None = field(
        default=None,
        metadata=wire("expires_seconds"),
    )
    wallet: Wallet | None = field(
        default=None,
        metadata=nested("wallet", lambda: Wallet),
    )
