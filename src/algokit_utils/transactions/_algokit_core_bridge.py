import base64

import algokit_transact
import algosdk.transaction


def build_payment_with_core(
    sender,
    sp,
    receiver,
    amt,
    close_remainder_to=None,
    note=None,
    lease=None,
    rekey_to=None,
) -> algosdk.transaction.PaymentTxn:
    txn = algokit_transact.Transaction(
        transaction_type=algokit_transact.TransactionType.PAYMENT,
        sender=algokit_transact.address_from_string(sender),
        # The correct fee will be calculated later based on suggested params and estimated size of the transaction.
        fee=sp.fee,
        first_valid=sp.first,
        last_valid=sp.last,
        genesis_hash=base64.b64decode(sp.gh),
        genesis_id=sp.gen,
        note=note,
        lease=lease,
        rekey_to=algokit_transact.address_from_string(rekey_to) if rekey_to else None,
        payment=algokit_transact.PaymentTransactionFields(
            receiver=algokit_transact.address_from_string(receiver),
            amount=amt,
            close_remainder_to=algokit_transact.address_from_string(close_remainder_to) if close_remainder_to else None,
        ),
    )

    size = algokit_transact.estimate_transaction_size(txn)
    final_fee: int
    if sp.flat_fee:
        final_fee = sp.fee
    else:
        min_fee = sp.min_fee or algosdk.constants.MIN_TXN_FEE
        final_fee = max(min_fee, sp.flat_fee * size)
    txn.fee = final_fee

    return algosdk.encoding.msgpack_decode(
        base64.b64encode(algokit_transact.encode_transaction_raw(txn)).decode("utf-8")
    )
