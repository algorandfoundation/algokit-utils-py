import nacl.signing
import pytest

from algokit_transact import (
    SignedTransaction,
    decode_signed_transactions,
    decode_transactions,
    encode_signed_transaction,
    encode_signed_transactions,
    encode_transaction,
    encode_transactions,
    group_transactions,
)

from .common import TransactionTestData
from .conftest import TestDataLookup

# Polytest Suite: Transaction Group

# Polytest Group: Transaction Group Tests


def _simple_group_test_data(test_data_lookup: TestDataLookup) -> list[TransactionTestData]:
    payment = test_data_lookup("simplePayment")
    opt_in = test_data_lookup("optInAssetTransfer")
    return [payment, opt_in]


def _sign(message: bytes, private_key: bytes) -> bytes:
    # Data factory SK is 64 bytes (Go's ed25519 format: 32-byte seed + 32-byte public)
    # NaCl expects just the 32-byte seed
    seed = private_key[:32]
    signing_key = nacl.signing.SigningKey(seed)
    return bytes(signing_key.sign(message).signature)


@pytest.mark.group_transaction_group_tests
def test_group_transactions(test_data_lookup: TestDataLookup) -> None:
    """A collection of transactions can be grouped"""
    vectors = _simple_group_test_data(test_data_lookup)
    grouped = group_transactions([v.transaction for v in vectors])

    assert len(grouped) == len(vectors)
    for original_vector, grouped_txn in zip(vectors, grouped, strict=False):
        assert original_vector.transaction.group is None
        # Verify that group is set (a 32-byte hash)
        assert grouped_txn.group is not None
        assert len(grouped_txn.group) == 32
    # Verify all transactions in the group have the same group ID
    group_ids = [txn.group for txn in grouped]
    assert all(g == group_ids[0] for g in group_ids)


@pytest.mark.group_transaction_group_tests
def test_encode_transactions(test_data_lookup: TestDataLookup) -> None:
    """A collection of transactions can be encoded"""
    vectors = _simple_group_test_data(test_data_lookup)
    grouped = group_transactions([v.transaction for v in vectors])
    encoded_grouped = encode_transactions(grouped)

    assert len(encoded_grouped) == len(grouped)
    for tx_bytes, tx in zip(encoded_grouped, grouped, strict=False):
        assert tx_bytes == encode_transaction(tx)

    decoded_grouped = decode_transactions(encoded_grouped)
    # Compare key fields since decoder may add default values
    assert len(decoded_grouped) == len(grouped)
    for decoded, original in zip(decoded_grouped, grouped, strict=False):
        assert decoded.transaction_type == original.transaction_type
        assert decoded.sender == original.sender
        assert decoded.group == original.group


@pytest.mark.group_transaction_group_tests
def test_encode_signed_transactions(test_data_lookup: TestDataLookup) -> None:
    """A collection of signed transactions can be encoded"""
    vectors = _simple_group_test_data(test_data_lookup)
    grouped = group_transactions([v.transaction for v in vectors])
    encoded_grouped = encode_transactions(grouped)

    signatures: list[bytes] = []
    for vector, tx_bytes in zip(vectors, encoded_grouped, strict=False):
        if vector.signer.single_signer is None:  # pragma: no cover - fixtures define keys
            raise AssertionError("missing signing key for test vector")
        signatures.append(_sign(tx_bytes, vector.signer.single_signer.sk))

    signed_grouped = [SignedTransaction(txn=tx, sig=sig) for tx, sig in zip(grouped, signatures, strict=False)]

    encoded_signed = encode_signed_transactions(signed_grouped)
    assert len(encoded_signed) == len(signed_grouped)

    for stx_bytes, stx in zip(encoded_signed, signed_grouped, strict=False):
        assert stx_bytes == encode_signed_transaction(stx)

    decoded_signed = decode_signed_transactions(encoded_signed)
    # Compare key fields
    assert len(decoded_signed) == len(signed_grouped)
    for decoded, original in zip(decoded_signed, signed_grouped, strict=False):
        assert decoded.txn.transaction_type == original.txn.transaction_type
        assert decoded.txn.sender == original.txn.sender
        assert decoded.sig == original.sig
