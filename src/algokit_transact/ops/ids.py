from algokit_common import base32_nopad_encode, sha512_256
from algokit_common.constants import TRANSACTION_ID_LENGTH
from algokit_transact.codec.transaction import encode_transaction
from algokit_transact.models.transaction import Transaction


def get_transaction_id_raw(transaction: Transaction) -> bytes:
    if transaction.genesis_hash is None:
        raise ValueError("Cannot compute transaction id without genesis hash")
    encoded = encode_transaction(transaction)
    return sha512_256(encoded)


def get_transaction_id(transaction: Transaction) -> str:
    raw = get_transaction_id_raw(transaction)
    return base32_nopad_encode(raw)[:TRANSACTION_ID_LENGTH]
