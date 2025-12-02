# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class CreateWalletRequest:
    """
    The request for `POST /v1/wallet`
    """

    wallet_name: str = field(
        default="",
        metadata=wire("wallet_name"),
    )
    wallet_password: str = field(
        default="",
        metadata=wire("wallet_password"),
    )
    master_derivation_key: list[int] | None = field(
        default=None,
        metadata=wire("master_derivation_key"),
    )
    wallet_driver_name: str | None = field(
        default="sqlite",
        metadata=wire("wallet_driver_name"),
    )
