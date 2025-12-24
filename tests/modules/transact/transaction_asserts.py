"""Helper assertions mirroring ``transaction_asserts.ts`` from TS suite."""

import nacl.signing

from algokit_transact import (
    SignedTransaction,
    apply_multisig_subsignature,
    assign_fee,
    decode_transaction,
    encode_signed_transaction,
    encode_transaction,
    encode_transaction_raw,
    estimate_transaction_size,
    get_encoded_transaction_type,
    get_transaction_id,
    merge_multisignatures,
    new_multisig_signature,
)

from .common import TransactionTestData


def _sign_ed25519(message: bytes, private_key: bytes) -> bytes:
    # Data factory SK is 64 bytes (Go's ed25519 format), take first 32 bytes as seed
    seed = private_key[:32]
    signing_key = nacl.signing.SigningKey(seed)
    signed = signing_key.sign(message)
    return bytes(signed.signature)


def _build_signed_transaction(
    *, txn: TransactionTestData, signature: bytes, auth_address: str | None = None
) -> SignedTransaction:
    return SignedTransaction(
        txn=txn.transaction,
        sig=signature,
        auth_address=auth_address,
    )


def assert_example(label: str, test_data: TransactionTestData) -> None:
    if test_data.signer.single_signer is None:
        # Skip tests that require single signer when not available
        return
    message = encode_transaction(test_data.transaction)
    signature = _sign_ed25519(message, test_data.signer.single_signer.sk)
    signed_txn = _build_signed_transaction(txn=test_data, signature=signature)
    encoded_signed = encode_signed_transaction(signed_txn)
    assert encoded_signed == test_data.signed_bytes, label


def assert_transaction_id(label: str, test_data: TransactionTestData) -> None:
    assert get_transaction_id(test_data.transaction) == test_data.id, label


def assert_encoded_transaction_type(label: str, test_data: TransactionTestData) -> None:
    # unsigned_bytes from data factory is raw msgpack without TX prefix
    encoded_type = get_encoded_transaction_type(test_data.unsigned_bytes)
    assert encoded_type == test_data.transaction.transaction_type, label


def assert_decode_without_prefix(label: str, test_data: TransactionTestData) -> None:
    # unsigned_bytes from data factory is already raw msgpack without prefix
    decoded = decode_transaction(test_data.unsigned_bytes)
    assert decoded == test_data.transaction, label


def assert_decode_with_prefix(label: str, test_data: TransactionTestData) -> None:
    # Add TX prefix to raw bytes for this test
    prefix = b"TX"
    with_prefix = prefix + test_data.unsigned_bytes
    decoded = decode_transaction(with_prefix)
    assert decoded == test_data.transaction, label


def assert_encode_with_signature(label: str, test_data: TransactionTestData) -> None:
    if test_data.signer.single_signer is None:
        # Skip tests that require single signer when not available
        return
    message = encode_transaction(test_data.transaction)
    signature = _sign_ed25519(message, test_data.signer.single_signer.sk)
    signed_txn = _build_signed_transaction(txn=test_data, signature=signature)
    encoded = encode_signed_transaction(signed_txn)
    assert encoded == test_data.signed_bytes, label


def assert_encode(label: str, test_data: TransactionTestData) -> None:
    """A transaction with valid fields is encoded properly."""
    # Use encode_transaction_raw which produces raw msgpack without TX prefix
    encoded = encode_transaction_raw(test_data.transaction)
    assert encoded == test_data.unsigned_bytes, label


def assert_assign_fee(label: str, test_data: TransactionTestData) -> None:
    min_fee = 2_000
    tx_with_min = assign_fee(test_data.transaction, fee_per_byte=0, min_fee=min_fee)
    assert tx_with_min.fee == min_fee, label

    extra_fee = 3_000
    tx_with_extra = assign_fee(test_data.transaction, fee_per_byte=0, min_fee=min_fee, extra_fee=extra_fee)
    assert tx_with_extra.fee == min_fee + extra_fee, label

    fee_per_byte = 100
    tx_with_byte_fee = assign_fee(test_data.transaction, fee_per_byte=fee_per_byte, min_fee=1_000)
    expected_fee = estimate_transaction_size(test_data.transaction) * fee_per_byte
    assert tx_with_byte_fee.fee == expected_fee, label


def assert_multisig_example(label: str, test_data: TransactionTestData) -> None:
    from algokit_common import address_from_public_key

    if test_data.signer.msig_signers is None or len(test_data.signer.msig_signers) < 2:
        # Skip - no multisig signers available
        return

    message = encode_transaction(test_data.transaction)

    # Get the first signer's private key for signing
    signature = _sign_ed25519(message, test_data.signer.msig_signers[0].sk)

    # Convert public keys to addresses for multisig
    participants = [address_from_public_key(s.pk) for s in test_data.signer.msig_signers]

    unsigned_multisig = new_multisig_signature(1, 2, participants)
    applied_signatures = [
        apply_multisig_subsignature(unsigned_multisig, participant, signature) for participant in participants
    ]
    merged = applied_signatures[0]
    for msig in applied_signatures[1:]:
        merged = merge_multisignatures(merged, msig)

    signed_txn = SignedTransaction(txn=test_data.transaction, msig=merged)
    encoded = encode_signed_transaction(signed_txn)
    assert encoded == test_data.signed_bytes, label
