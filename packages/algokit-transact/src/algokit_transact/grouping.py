from __future__ import annotations

from collections import OrderedDict
from collections.abc import Iterable
from dataclasses import replace

import msgpack

from .constants import TRANSACTION_GROUP_DOMAIN_SEPARATOR
from .hashing import sha512_256
from .ids import get_transaction_id_raw
from .types import Transaction


def group_transactions(transactions: Iterable[Transaction]) -> list[Transaction]:
    txs = list(transactions)
    if not txs:
        raise ValueError("Transaction group size cannot be 0")

    # Compute hashes (includes TX prefix semantics)
    tx_hashes = []
    for tx in txs:
        if tx.group is not None:
            raise ValueError("Transactions must not already be grouped")
        tx_hashes.append(get_transaction_id_raw(tx))

    payload = OrderedDict([("txlist", tx_hashes)])
    encoded = msgpack.packb(payload, use_bin_type=True, strict_types=True)
    group = sha512_256(TRANSACTION_GROUP_DOMAIN_SEPARATOR.encode() + encoded)

    # assign group, preserving immutability by recreating dataclasses
    return [replace(tx, group=group) for tx in txs]
