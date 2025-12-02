# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class RenameWalletRequest:
    """
    The request for `POST /v1/wallet/rename`
    """

    wallet_id: str = field(
        default="",
        metadata=wire("wallet_id"),
    )
    wallet_name: str = field(
        default="",
        metadata=wire("wallet_name"),
    )
    wallet_password: str = field(
        default="",
        metadata=wire("wallet_password"),
    )
