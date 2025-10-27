from __future__ import annotations

from dataclasses import dataclass, field

from algokit_common.serde import nested, wire
from algokit_transact.models.signed_transaction import SignedTransaction

from ._serde_helpers import decode_model_sequence, encode_model_sequence
from .account_state_delta import AccountStateDelta
from .eval_delta_key_value import EvalDeltaKeyValue


@dataclass(slots=True)
class PendingTransactionResponse:
    """
    Details about a pending transaction. If the transaction was recently confirmed, includes
    confirmation details like the round and reward details.
    """

    pool_error: str = field(
        metadata=wire("pool-error"),
    )
    txn: SignedTransaction = field(
        metadata=nested("txn", lambda: SignedTransaction),
    )
    app_id: int | None = field(
        default=None,
        metadata=wire("app_id"),
    )
    asset_closing_amount: int | None = field(
        default=None,
        metadata=wire("asset-closing-amount"),
    )
    asset_id: int | None = field(
        default=None,
        metadata=wire("asset_id"),
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
    inner_txns: list[PendingTransactionResponse] | None = field(
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
        metadata=wire("logs"),
    )
    receiver_rewards: int | None = field(
        default=None,
        metadata=wire("receiver-rewards"),
    )
    sender_rewards: int | None = field(
        default=None,
        metadata=wire("sender-rewards"),
    )
