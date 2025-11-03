import nacl.signing

from algokit_common import MAX_TX_GROUP_SIZE
from algokit_transact import (
    SignedTransaction,
    TransactionType,
    decode_signed_transactions,
    decode_transactions,
    encode_signed_transaction,
    encode_signed_transactions,
    encode_transaction,
    encode_transactions,
    group_transactions,
)

from .common import TransactionVector
from .conftest import VectorLookup

EXPECTED_GROUP_ID = bytes(
    [
        202,
        79,
        82,
        7,
        197,
        237,
        213,
        55,
        117,
        226,
        131,
        74,
        221,
        85,
        86,
        215,
        64,
        133,
        212,
        7,
        58,
        234,
        248,
        162,
        222,
        53,
        161,
        29,
        141,
        101,
        133,
        49,
    ]
)


def _simple_group_vectors(vector_lookup: VectorLookup) -> list[TransactionVector]:
    payment = vector_lookup("simplePayment")
    opt_in = vector_lookup("optInAssetTransfer")
    return [payment, opt_in]


def _sign(message: bytes, private_key: bytes) -> bytes:
    signing_key = nacl.signing.SigningKey(private_key)
    return bytes(signing_key.sign(message).signature)


def test_group_transactions(vector_lookup: VectorLookup) -> None:
    vectors = _simple_group_vectors(vector_lookup)
    grouped = group_transactions([v.transaction for v in vectors])

    assert len(grouped) == len(vectors)
    for original_vector, grouped_txn in zip(vectors, grouped, strict=False):
        assert original_vector.transaction.group is None
        assert grouped_txn.group == EXPECTED_GROUP_ID


def test_group_transactions_max_size(vector_lookup: VectorLookup) -> None:
    vectors = _simple_group_vectors(vector_lookup)
    base = vectors[0].transaction
    # Create MAX_TX_GROUP_SIZE + 1 copies (with different first_valid to avoid identical txs)
    over_limit = [
        base.__class__(
            transaction_type=TransactionType.Payment,
            sender=base.sender,
            first_valid=base.first_valid + i,
            last_valid=base.last_valid + i,
            payment=base.payment,
        )
        for i in range(MAX_TX_GROUP_SIZE + 1)
    ]

    import pytest

    with pytest.raises(ValueError, match=rf"max limit of {MAX_TX_GROUP_SIZE}"):
        group_transactions(over_limit)


def test_encode_transactions(vector_lookup: VectorLookup) -> None:
    vectors = _simple_group_vectors(vector_lookup)
    grouped = group_transactions([v.transaction for v in vectors])
    encoded_grouped = encode_transactions(grouped)

    assert len(encoded_grouped) == len(grouped)
    for tx_bytes, tx in zip(encoded_grouped, grouped, strict=False):
        assert tx_bytes == encode_transaction(tx)

    decoded_grouped = decode_transactions(encoded_grouped)
    assert decoded_grouped == grouped


def test_encode_signed_transactions(vector_lookup: VectorLookup) -> None:
    vectors = _simple_group_vectors(vector_lookup)
    grouped = group_transactions([v.transaction for v in vectors])
    encoded_grouped = encode_transactions(grouped)

    signatures: list[bytes] = []
    for vector, tx_bytes in zip(vectors, encoded_grouped, strict=False):
        if vector.signing_private_key is None:  # pragma: no cover - fixtures define keys
            raise AssertionError("missing signing key for test vector")
        signatures.append(_sign(tx_bytes, vector.signing_private_key))

    signed_grouped = [
        SignedTransaction(transaction=tx, signature=sig) for tx, sig in zip(grouped, signatures, strict=False)
    ]

    encoded_signed = encode_signed_transactions(signed_grouped)
    assert len(encoded_signed) == len(signed_grouped)

    for stx_bytes, stx in zip(encoded_signed, signed_grouped, strict=False):
        assert stx_bytes == encode_signed_transaction(stx)

    decoded_signed = decode_signed_transactions(encoded_signed)
    assert decoded_signed == signed_grouped
