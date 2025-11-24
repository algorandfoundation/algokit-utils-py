from algokit_transact.models.payment import PaymentTransactionFields
from algokit_transact.models.transaction import TransactionType
from algokit_utils.transactions.builders.common import (
    BuiltTransaction,
    SuggestedParamsLike,
    apply_transaction_fees,
    build_transaction,
    build_transaction_header,
)
from algokit_utils.transactions.types import PaymentParams

__all__ = ["build_payment_transaction"]


def build_payment_transaction(
    params: PaymentParams,
    suggested_params: SuggestedParamsLike,
    *,
    default_validity_window: int,
    default_validity_window_is_explicit: bool,
    is_localnet: bool,
) -> BuiltTransaction:
    header, fee_config = build_transaction_header(
        params,
        suggested_params,
        default_validity_window=default_validity_window,
        default_validity_window_is_explicit=default_validity_window_is_explicit,
        is_localnet=is_localnet,
    )

    payment_fields = PaymentTransactionFields(
        amount=params.amount.micro_algo,
        receiver=params.receiver,
        close_remainder_to=params.close_remainder_to,
    )

    txn = build_transaction(
        TransactionType.Payment,
        header,
        payment=payment_fields,
    )

    return apply_transaction_fees(txn, params, fee_config)
