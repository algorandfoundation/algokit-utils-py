# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.constants import ZERO_ADDRESS
from algokit_common.serde import wire


@dataclass(slots=True)
class ExportMultisigRequest:
    """
    The request for `POST /v1/multisig/export`
    """

    address: str = field(
        default=ZERO_ADDRESS,
        metadata=wire("address"),
    )
    wallet_handle_token: str = field(
        default="",
        metadata=wire("wallet_handle_token"),
    )
