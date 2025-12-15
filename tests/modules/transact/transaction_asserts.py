"""Helper assertions mirroring ``transaction_asserts.ts`` from TS suite."""

import nacl.signing

from algokit_transact import (
    SignedTransaction,
    apply_multisig_subsignature,
    assign_fee,
    decode_transaction,
    encode_signed_transaction,
    encode_transaction,
    estimate_transaction_size,
    get_encoded_transaction_type,
    get_transaction_id,
    get_transaction_id_raw,
    merge_multisignatures,
    new_multisig_signature,
)

from .common import TransactionVector


def _sign_ed25519(message: bytes, private_key: bytes) -> bytes:
    signing_key = nacl.signing.SigningKey(private_key)
    signed = signing_key.sign(message)
    return bytes(signed.signature)


def _ensure_bytes(name: str, value: bytes | None, label: str) -> bytes:
    if value is None:
        raise ValueError(f"{label}: missing byte payload for {name}")
    return value


def _build_signed_transaction(
    *, txn: TransactionVector, signature: bytes, auth_address: str | None = None
) -> SignedTransaction:
    return SignedTransaction(
        txn=txn.transaction,
        sig=signature,
        auth_address=auth_address,
    )


def assert_example(label: str, test_data: TransactionVector) -> None:
    message = encode_transaction(test_data.transaction)
    signature = _sign_ed25519(message, _ensure_bytes("signingPrivateKey", test_data.signing_private_key, label))
    signed_txn = _build_signed_transaction(txn=test_data, signature=signature)
    encoded_signed = encode_signed_transaction(signed_txn)
    assert encoded_signed == _ensure_bytes("signedBytes", test_data.signed_bytes, label), label


def assert_transaction_id(label: str, test_data: TransactionVector) -> None:
    expected_raw = _ensure_bytes("idRaw", test_data.id_raw, label)
    expected_str = test_data.id
    assert expected_str is not None
    assert get_transaction_id_raw(test_data.transaction) == expected_raw, label
    assert get_transaction_id(test_data.transaction) == expected_str, label


def assert_encoded_transaction_type(label: str, test_data: TransactionVector) -> None:
    encoded_type = get_encoded_transaction_type(test_data.unsigned_bytes)
    assert encoded_type == test_data.transaction.transaction_type, label


def assert_decode_without_prefix(label: str, test_data: TransactionVector) -> None:
    decoded = decode_transaction(test_data.unsigned_bytes[2:])
    assert decoded == test_data.transaction, label


def assert_decode_with_prefix(label: str, test_data: TransactionVector) -> None:
    decoded = decode_transaction(test_data.unsigned_bytes)
    assert decoded == test_data.transaction, label


def assert_encode_with_auth_address(label: str, test_data: TransactionVector) -> None:
    message = encode_transaction(test_data.transaction)
    signature = _sign_ed25519(message, _ensure_bytes("signingPrivateKey", test_data.signing_private_key, label))
    signed_txn = _build_signed_transaction(
        txn=test_data,
        signature=signature,
        auth_address=test_data.rekeyed_sender_auth_address,
    )
    encoded = encode_signed_transaction(signed_txn)
    assert encoded == _ensure_bytes("rekeyedSenderSignedBytes", test_data.rekeyed_sender_signed_bytes, label), label


def assert_encode_with_signature(label: str, test_data: TransactionVector) -> None:
    message = encode_transaction(test_data.transaction)
    signature = _sign_ed25519(message, _ensure_bytes("signingPrivateKey", test_data.signing_private_key, label))
    signed_txn = _build_signed_transaction(txn=test_data, signature=signature)
    encoded = encode_signed_transaction(signed_txn)
    assert encoded == _ensure_bytes("signedBytes", test_data.signed_bytes, label), label


def assert_encode(label: str, test_data: TransactionVector) -> None:
    encoded = encode_transaction(test_data.transaction)
    assert encoded == test_data.unsigned_bytes, label


def assert_assign_fee(label: str, test_data: TransactionVector) -> None:
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


def assert_multisig_example(label: str, test_data: TransactionVector) -> None:
    message = encode_transaction(test_data.transaction)
    signature = _sign_ed25519(message, _ensure_bytes("signingPrivateKey", test_data.signing_private_key, label))

    participants = test_data.multisig_addresses
    if not participants:
        raise ValueError("Test vector missing multisig addresses")

    unsigned_multisig = new_multisig_signature(1, 2, participants)
    applied_signatures = [
        apply_multisig_subsignature(unsigned_multisig, participant, signature) for participant in participants
    ]
    merged = applied_signatures[0]
    for msig in applied_signatures[1:]:
        merged = merge_multisignatures(merged, msig)

    signed_txn = SignedTransaction(txn=test_data.transaction, msig=merged)
    encoded = encode_signed_transaction(signed_txn)
    assert encoded == _ensure_bytes("multisigSignedBytes", test_data.multisig_signed_bytes, label), label
