# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire

from ._ledger_state_delta_for_transaction_group import LedgerStateDeltaForTransactionGroup
from ._serde_helpers import decode_model_sequence, encode_model_sequence


@dataclass(slots=True)
class GetTransactionGroupLedgerStateDeltasForRoundResponseModel:
    deltas: list[LedgerStateDeltaForTransactionGroup] = field(
        metadata=wire(
            "Deltas",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: LedgerStateDeltaForTransactionGroup, raw),
        ),
    )
