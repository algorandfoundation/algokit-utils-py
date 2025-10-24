from __future__ import annotations

from collections.abc import Iterable
from dataclasses import replace

from .constants import MAX_TX_GROUP_SIZE, TRANSACTION_GROUP_DOMAIN_SEPARATOR
from .hashing import sha512_256
from .ids import get_transaction_id_raw
from .msgpack_utils import encode_msgpack
from .types import Transaction


def group_transactions(transactions: Iterable[Transaction]) -> list[Transaction]:
    txs = list(transactions)
    if not txs:
        raise ValueError("Transaction group size cannot be 0")
    if len(txs) > MAX_TX_GROUP_SIZE:
        raise ValueError(f"Transaction group size exceeds the max limit of {MAX_TX_GROUP_SIZE}")

    # Compute hashes (includes TX prefix semantics)
    tx_hashes = []
    for tx in txs:
        if tx.group is not None:
            raise ValueError("Transactions must not already be grouped")
        tx_hashes.append(get_transaction_id_raw(tx))

    encoded = encode_msgpack({"txlist": tx_hashes})
    group = sha512_256(TRANSACTION_GROUP_DOMAIN_SEPARATOR.encode() + encoded)

    # assign group, preserving immutability by recreating dataclasses
    return [replace(tx, group=group) for tx in txs]
