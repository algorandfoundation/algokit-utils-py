from __future__ import annotations

from dataclasses import dataclass, field

from algokit_transact.codec.serde import addr, wire


@dataclass(slots=True, frozen=True)
class PaymentTransactionFields:
    amount: int = field(metadata=wire("amt"))
    receiver: str = field(metadata=addr("rcv"))
    close_remainder_to: str | None = field(
        default=None,
        metadata=addr("close", omit_if_none=True),
    )
