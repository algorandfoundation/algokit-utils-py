# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class WalletInfoRequest:
    """
    The request for `POST /v1/wallet/info`
    """

    wallet_handle_token: str = field(
        default="",
        metadata=wire("wallet_handle_token"),
    )
