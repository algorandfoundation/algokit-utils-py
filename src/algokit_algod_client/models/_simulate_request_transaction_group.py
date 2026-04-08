# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire
from algokit_transact.models.signed_transaction import SignedTransaction

from ._serde_helpers import decode_model_sequence, encode_model_sequence


@dataclass(slots=True)
class SimulateRequestTransactionGroup:
    """
    A transaction group to simulate.
    """

    txns: list[SignedTransaction] = field(
        default_factory=list,
        metadata=wire(
            "txns",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: SignedTransaction, raw),
        ),
    )
