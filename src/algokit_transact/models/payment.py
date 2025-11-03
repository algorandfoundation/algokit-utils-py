from dataclasses import dataclass, field

from algokit_common.constants import ZERO_ADDRESS
from algokit_transact.codec.serde import addr, wire


@dataclass(slots=True, frozen=True)
class PaymentTransactionFields:
    amount: int = field(default=0, metadata=wire("amt"))
    receiver: str = field(default=ZERO_ADDRESS, metadata=addr("rcv"))
    close_remainder_to: str | None = field(
        default=None,
        metadata=addr("close", omit_if_none=True),
    )
