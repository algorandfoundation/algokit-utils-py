# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import nested, wire
from algokit_transact.models.signed_transaction import SignedTransaction

from ._account_state_delta import AccountStateDelta
from ._eval_delta_key_value import EvalDeltaKeyValue
from ._serde_helpers import (
    decode_bytes_sequence,
    decode_model_sequence,
    encode_bytes_sequence,
    encode_model_sequence,
)


@dataclass(slots=True)
class PendingTransactionResponse:
    """
    Details about a pending transaction. If the transaction was recently confirmed, includes
    confirmation details like the round and reward details.
    """

    txn: SignedTransaction = field(
        metadata=nested("txn", lambda: SignedTransaction, required=True),
    )
    pool_error: str = field(
        default="",
        metadata=wire("pool-error"),
    )
    app_id: int | None = field(
        default=None,
        metadata=wire("application-index"),
    )
    asset_closing_amount: int | None = field(
        default=None,
        metadata=wire("asset-closing-amount"),
    )
    asset_id: int | None = field(
        default=None,
        metadata=wire("asset-index"),
    )
    close_rewards: int | None = field(
        default=None,
        metadata=wire("close-rewards"),
    )
    closing_amount: int | None = field(
        default=None,
        metadata=wire("closing-amount"),
    )
    confirmed_round: int | None = field(
        default=None,
        metadata=wire("confirmed-round"),
    )
    global_state_delta: list[EvalDeltaKeyValue] | None = field(
        default=None,
        metadata=wire(
            "global-state-delta",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: EvalDeltaKeyValue, raw),
        ),
    )
    inner_txns: list["PendingTransactionResponse"] | None = field(
        default=None,
        metadata=wire(
            "inner-txns",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: PendingTransactionResponse, raw),
        ),
    )
    local_state_delta: list[AccountStateDelta] | None = field(
        default=None,
        metadata=wire(
            "local-state-delta",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: AccountStateDelta, raw),
        ),
    )
    logs: list[bytes] | None = field(
        default=None,
        metadata=wire(
            "logs",
            encode=encode_bytes_sequence,
            decode=decode_bytes_sequence,
        ),
    )
    receiver_rewards: int | None = field(
        default=None,
        metadata=wire("receiver-rewards"),
    )
    sender_rewards: int | None = field(
        default=None,
        metadata=wire("sender-rewards"),
    )
