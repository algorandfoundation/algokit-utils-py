import pytest

from algokit_transact import TransactionValidationError, validate_transaction

from ._helpers import iter_key_registration_vectors
from ._validation import build_key_registration, clone_transaction
from .conftest import VectorLookup
from .transaction_asserts import (
    assert_assign_fee,
    assert_decode_with_prefix,
    assert_decode_without_prefix,
    assert_encode,
    assert_encode_with_auth_address,
    assert_encode_with_signature,
    assert_encoded_transaction_type,
    assert_example,
    assert_multisig_example,
    assert_transaction_id,
)

ZERO32 = b"\x00" * 32
ZERO64 = b"\x00" * 64


@pytest.mark.parametrize(("label", "key"), list(iter_key_registration_vectors()))
def test_example(label: str, key: str, vector_lookup: VectorLookup) -> None:
    assert_example(label, vector_lookup(key))


@pytest.mark.parametrize(("label", "key"), list(iter_key_registration_vectors()))
def test_multisig_example(label: str, key: str, vector_lookup: VectorLookup) -> None:
    assert_multisig_example(label, vector_lookup(key))


@pytest.mark.parametrize(("label", "key"), list(iter_key_registration_vectors()))
def test_get_transaction_id(label: str, key: str, vector_lookup: VectorLookup) -> None:
    assert_transaction_id(label, vector_lookup(key))


@pytest.mark.parametrize(("label", "key"), list(iter_key_registration_vectors()))
def test_assign_fee(label: str, key: str, vector_lookup: VectorLookup) -> None:
    assert_assign_fee(label, vector_lookup(key))


@pytest.mark.parametrize(("label", "key"), list(iter_key_registration_vectors()))
def test_get_encoded_transaction_type(label: str, key: str, vector_lookup: VectorLookup) -> None:
    assert_encoded_transaction_type(label, vector_lookup(key))


@pytest.mark.parametrize(("label", "key"), list(iter_key_registration_vectors()))
def test_decode_without_prefix(label: str, key: str, vector_lookup: VectorLookup) -> None:
    assert_decode_without_prefix(label, vector_lookup(key))


@pytest.mark.parametrize(("label", "key"), list(iter_key_registration_vectors()))
def test_decode_with_prefix(label: str, key: str, vector_lookup: VectorLookup) -> None:
    assert_decode_with_prefix(label, vector_lookup(key))


@pytest.mark.parametrize(("label", "key"), list(iter_key_registration_vectors()))
def test_encode_with_auth_address(label: str, key: str, vector_lookup: VectorLookup) -> None:
    assert_encode_with_auth_address(label, vector_lookup(key))


@pytest.mark.parametrize(("label", "key"), list(iter_key_registration_vectors()))
def test_encode_with_signature(label: str, key: str, vector_lookup: VectorLookup) -> None:
    assert_encode_with_signature(label, vector_lookup(key))


@pytest.mark.parametrize(("label", "key"), list(iter_key_registration_vectors()))
def test_encode(label: str, key: str, vector_lookup: VectorLookup) -> None:
    assert_encode(label, vector_lookup(key))


def test_should_throw_error_when_vote_key_missing(vector_lookup: VectorLookup) -> None:
    vector = vector_lookup("onlineKeyRegistration")
    tx = clone_transaction(
        vector.transaction,
        key_registration=build_key_registration(
            selection_key=ZERO32,
            state_proof_key=ZERO64,
            vote_first=1000,
            vote_last=2000,
            vote_key_dilution=10000,
        ),
    )

    with pytest.raises(TransactionValidationError) as exc:
        validate_transaction(tx)
    assert "Vote key is required" in str(exc.value)


def test_should_throw_error_when_selection_key_missing(vector_lookup: VectorLookup) -> None:
    vector = vector_lookup("onlineKeyRegistration")
    tx = clone_transaction(
        vector.transaction,
        key_registration=build_key_registration(
            vote_key=ZERO32,
            state_proof_key=ZERO64,
            vote_first=1000,
            vote_last=2000,
            vote_key_dilution=10000,
        ),
    )

    with pytest.raises(TransactionValidationError) as exc:
        validate_transaction(tx)
    assert "Selection key is required" in str(exc.value)


def test_should_throw_error_when_state_proof_key_missing(vector_lookup: VectorLookup) -> None:
    vector = vector_lookup("onlineKeyRegistration")
    tx = clone_transaction(
        vector.transaction,
        key_registration=build_key_registration(
            vote_key=ZERO32,
            selection_key=ZERO32,
            vote_first=1000,
            vote_last=2000,
            vote_key_dilution=10000,
        ),
    )

    with pytest.raises(TransactionValidationError) as exc:
        validate_transaction(tx)
    assert "State proof key is required" in str(exc.value)


def test_should_throw_error_when_vote_first_missing(vector_lookup: VectorLookup) -> None:
    vector = vector_lookup("onlineKeyRegistration")
    tx = clone_transaction(
        vector.transaction,
        key_registration=build_key_registration(
            vote_key=ZERO32,
            selection_key=ZERO32,
            state_proof_key=ZERO64,
            vote_last=2000,
            vote_key_dilution=10000,
        ),
    )

    with pytest.raises(TransactionValidationError) as exc:
        validate_transaction(tx)
    assert "Vote first is required" in str(exc.value)


def test_should_throw_error_when_vote_last_missing(vector_lookup: VectorLookup) -> None:
    vector = vector_lookup("onlineKeyRegistration")
    tx = clone_transaction(
        vector.transaction,
        key_registration=build_key_registration(
            vote_key=ZERO32,
            selection_key=ZERO32,
            state_proof_key=ZERO64,
            vote_first=1000,
            vote_key_dilution=10000,
        ),
    )

    with pytest.raises(TransactionValidationError) as exc:
        validate_transaction(tx)
    assert "Vote last is required" in str(exc.value)


def test_should_throw_error_when_vote_key_dilution_missing(vector_lookup: VectorLookup) -> None:
    vector = vector_lookup("onlineKeyRegistration")
    tx = clone_transaction(
        vector.transaction,
        key_registration=build_key_registration(
            vote_key=ZERO32,
            selection_key=ZERO32,
            state_proof_key=ZERO64,
            vote_first=1000,
            vote_last=2000,
        ),
    )

    with pytest.raises(TransactionValidationError) as exc:
        validate_transaction(tx)
    assert "Vote key dilution is required" in str(exc.value)


def test_should_throw_error_when_vote_first_not_less_than_vote_last(vector_lookup: VectorLookup) -> None:
    vector = vector_lookup("onlineKeyRegistration")
    tx = clone_transaction(
        vector.transaction,
        key_registration=build_key_registration(
            vote_key=ZERO32,
            selection_key=ZERO32,
            state_proof_key=ZERO64,
            vote_first=2000,
            vote_last=2000,
            vote_key_dilution=10000,
        ),
    )

    with pytest.raises(TransactionValidationError) as exc:
        validate_transaction(tx)
    assert "Vote first must be less than vote last" in str(exc.value)


def test_should_throw_error_when_vote_first_greater_than_vote_last(vector_lookup: VectorLookup) -> None:
    vector = vector_lookup("onlineKeyRegistration")
    tx = clone_transaction(
        vector.transaction,
        key_registration=build_key_registration(
            vote_key=ZERO32,
            selection_key=ZERO32,
            state_proof_key=ZERO64,
            vote_first=3000,
            vote_last=2000,
            vote_key_dilution=10000,
        ),
    )

    with pytest.raises(TransactionValidationError) as exc:
        validate_transaction(tx)
    assert "Vote first must be less than vote last" in str(exc.value)


def test_should_throw_error_when_non_participation_set_for_online_registration(vector_lookup: VectorLookup) -> None:
    vector = vector_lookup("onlineKeyRegistration")
    tx = clone_transaction(
        vector.transaction,
        key_registration=build_key_registration(
            vote_key=ZERO32,
            selection_key=ZERO32,
            state_proof_key=ZERO64,
            vote_first=1000,
            vote_last=2000,
            vote_key_dilution=10000,
            non_participation=True,
        ),
    )

    with pytest.raises(TransactionValidationError) as exc:
        validate_transaction(tx)
    assert "Online key registration cannot have non participation flag set" in str(exc.value)


def test_should_throw_multiple_errors_for_online_registration(vector_lookup: VectorLookup) -> None:
    vector = vector_lookup("onlineKeyRegistration")
    tx = clone_transaction(
        vector.transaction,
        key_registration=build_key_registration(
            vote_first=2000,
            vote_last=1000,
            non_participation=True,
        ),
    )

    with pytest.raises(TransactionValidationError) as exc:
        validate_transaction(tx)
    message = str(exc.value)
    assert "Vote key is required" in message
    assert "Selection key is required" in message
    assert "State proof key is required" in message
    assert "Vote first must be less than vote last" in message
    assert "Vote key dilution is required" in message
    assert "Online key registration cannot have non participation flag set" in message


def test_should_validate_valid_online_registration_transaction(vector_lookup: VectorLookup) -> None:
    vector = vector_lookup("onlineKeyRegistration")
    tx = clone_transaction(
        vector.transaction,
        key_registration=build_key_registration(
            vote_key=ZERO32,
            selection_key=ZERO32,
            state_proof_key=ZERO64,
            vote_first=1000,
            vote_last=2000,
            vote_key_dilution=10000,
        ),
    )

    validate_transaction(tx)


def test_should_validate_online_registration_with_non_participation_false(vector_lookup: VectorLookup) -> None:
    vector = vector_lookup("onlineKeyRegistration")
    tx = clone_transaction(
        vector.transaction,
        key_registration=build_key_registration(
            vote_key=ZERO32,
            selection_key=ZERO32,
            state_proof_key=ZERO64,
            vote_first=1000,
            vote_last=2000,
            vote_key_dilution=10000,
            non_participation=False,
        ),
    )

    validate_transaction(tx)


def test_should_validate_offline_key_registration(vector_lookup: VectorLookup) -> None:
    vector = vector_lookup("offlineKeyRegistration")
    validate_transaction(vector.transaction)


def test_should_validate_non_participation_registration(vector_lookup: VectorLookup) -> None:
    vector = vector_lookup("nonParticipationKeyRegistration")
    validate_transaction(vector.transaction)


def test_should_validate_offline_key_registration_with_non_participation_false(vector_lookup: VectorLookup) -> None:
    vector = vector_lookup("offlineKeyRegistration")
    tx = clone_transaction(
        vector.transaction,
        key_registration=build_key_registration(
            non_participation=False,
        ),
    )

    validate_transaction(tx)
