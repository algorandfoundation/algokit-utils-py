# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import nested

from ._wallet import Wallet


@dataclass(slots=True)
class RenameWalletResponse:
    """
    RenameWalletResponse is the response to `POST /v1/wallet/rename`
    """

    wallet: Wallet = field(
        metadata=nested("wallet", lambda: Wallet, required=True),
    )
