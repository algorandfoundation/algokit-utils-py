# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class InitWalletHandleTokenRequest:
    """
    The request for `POST /v1/wallet/init`
    """

    wallet_id: str = field(
        default="",
        metadata=wire("wallet_id"),
    )
    wallet_password: str = field(
        default="",
        metadata=wire("wallet_password"),
    )
