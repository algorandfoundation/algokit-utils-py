# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.constants import ZERO_ADDRESS
from algokit_common.serde import wire


@dataclass(slots=True)
class DeleteMultisigRequest:
    """
    The request for `DELETE /v1/multisig`
    """

    address: str = field(
        default=ZERO_ADDRESS,
        metadata=wire("address"),
    )
    wallet_handle_token: str = field(
        default="",
        metadata=wire("wallet_handle_token"),
    )
    wallet_password: str | None = field(
        default=None,
        metadata=wire("wallet_password"),
    )
