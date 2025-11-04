# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class CreateWalletRequest:
    """
    APIV1POSTWalletRequest is the request for `POST /v1/wallet`
    """

    master_derivation_key: list[int] | None = field(
        default=None,
        metadata=wire("master_derivation_key"),
    )
    wallet_driver_name: str | None = field(
        default=None,
        metadata=wire("wallet_driver_name"),
    )
    wallet_name: str | None = field(
        default=None,
        metadata=wire("wallet_name"),
    )
    wallet_password: str | None = field(
        default=None,
        metadata=wire("wallet_password"),
    )
