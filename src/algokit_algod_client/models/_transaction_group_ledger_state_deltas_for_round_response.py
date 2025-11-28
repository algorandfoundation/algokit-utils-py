# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire

from ._ledger_state_delta import LedgerStateDeltaForTransactionGroup
from ._serde_helpers import decode_model_sequence, encode_model_sequence


@dataclass(slots=True)
class TransactionGroupLedgerStateDeltasForRoundResponse:
    deltas: list[LedgerStateDeltaForTransactionGroup] = field(
        default_factory=list,
        metadata=wire(
            "Deltas",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: LedgerStateDeltaForTransactionGroup, raw),
        ),
    )
