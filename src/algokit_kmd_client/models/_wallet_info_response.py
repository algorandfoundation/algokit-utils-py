# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import nested

from ._wallet_handle import WalletHandle


@dataclass(slots=True)
class WalletInfoResponse:
    """
    WalletInfoResponse is the response to `POST /v1/wallet/info`
    """

    wallet_handle: WalletHandle = field(
        metadata=nested("wallet_handle", lambda: WalletHandle, required=True),
    )
