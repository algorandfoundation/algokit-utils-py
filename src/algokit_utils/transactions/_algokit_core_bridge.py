import base64
from typing import cast

import algosdk.transaction
from algokit_transact import (
    FeeParams,
    PaymentTransactionFields,
    Transaction,
    TransactionType,
    address_from_string,
    assign_fee,
    encode_transaction_raw,
)


def build_payment_with_core(  # noqa: PLR0913
    sender,
    sp,
    receiver,
    amt,
    close_remainder_to=None,
    note=None,
    lease=None,
    rekey_to=None,
    static_fee=None,
    max_fee=None,
    extra_fee=None,
) -> algosdk.transaction.PaymentTxn:
    # Determine static fee based on parameters or suggested params
    static_fee_value = None
    if static_fee is not None:
        static_fee_value = static_fee
    elif sp.flat_fee:
        static_fee_value = sp.fee

    txn = Transaction(
        transaction_type=TransactionType.PAYMENT,
        sender=address_from_string(sender),
        fee=static_fee_value,
        first_valid=sp.first,
        last_valid=sp.last,
        genesis_hash=base64.b64decode(sp.gh),
        genesis_id=sp.gen,
        note=note,
        lease=lease,
        rekey_to=address_from_string(rekey_to) if rekey_to else None,
        payment=PaymentTransactionFields(
            receiver=address_from_string(receiver),
            amount=amt,
            close_remainder_to=address_from_string(close_remainder_to) if close_remainder_to else None,
        ),
    )

    if txn.fee is not None:
        # Static fee is already set, encode and return directly
        return cast(
            algosdk.transaction.PaymentTxn,
            algosdk.encoding.msgpack_decode(base64.b64encode(encode_transaction_raw(txn)).decode("utf-8")),
        )
    else:
        # Use assign_fee with fee parameters
        min_fee = sp.min_fee or algosdk.constants.MIN_TXN_FEE
        txn_with_fee = assign_fee(
            txn,
            FeeParams(
                fee_per_byte=sp.fee,
                min_fee=min_fee,
                max_fee=max_fee,
                extra_fee=extra_fee,
            ),
        )

        return cast(
            algosdk.transaction.PaymentTxn,
            algosdk.encoding.msgpack_decode(base64.b64encode(encode_transaction_raw(txn_with_fee)).decode("utf-8")),
        )
