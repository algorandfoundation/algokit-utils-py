# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class RawTransactionResponseModel:
    tx_id: str = field(
        metadata=wire("txId"),
    )
