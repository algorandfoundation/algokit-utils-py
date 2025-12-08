# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class InitWalletHandleTokenResponse:
    """
    InitWalletHandleTokenResponse is the response to `POST /v1/wallet/init`
    """

    wallet_handle_token: str = field(
        default="",
        metadata=wire("wallet_handle_token"),
    )
