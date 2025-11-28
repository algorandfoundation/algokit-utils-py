# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class PostTransactionsResponse:
    tx_id: str = field(
        default="",
        metadata=wire("txId"),
    )
