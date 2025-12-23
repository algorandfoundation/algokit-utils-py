from collections.abc import Iterable
from dataclasses import replace

from algokit_common import sha512_256
from algokit_common.constants import MAX_TRANSACTION_GROUP_SIZE, TRANSACTION_GROUP_DOMAIN_SEPARATOR
from algokit_transact.codec.msgpack import encode_msgpack
from algokit_transact.models.transaction import Transaction
from algokit_transact.ops.ids import get_transaction_id_raw


def group_transactions(transactions: Iterable[Transaction]) -> list[Transaction]:
    txs = list(transactions)

    if not txs:
        raise ValueError("Transaction group cannot be empty")
    if len(txs) > MAX_TRANSACTION_GROUP_SIZE:
        raise ValueError(f"Transaction group size exceeds the max limit of {MAX_TRANSACTION_GROUP_SIZE}")

    tx_hashes = []
    for tx in txs:
        if tx.group is not None:
            raise ValueError("Transactions must not already be grouped")
        tx_hashes.append(get_transaction_id_raw(tx))

    encoded = encode_msgpack({"txlist": tx_hashes})
    group = sha512_256(TRANSACTION_GROUP_DOMAIN_SEPARATOR + encoded)

    return [replace(tx, group=group) for tx in txs]
