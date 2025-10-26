from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from algokit_transact import (
    BoxReference,
    OnApplicationComplete,
    StateSchema,
    Transaction,
    decode_transaction,
    encode_transaction,
    validate_transaction,
)

from tests._helpers import iter_app_call_vectors
from tests._validation import assert_validation_error, build_app_call, clone_transaction
from tests.transaction_asserts import (
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

if TYPE_CHECKING:
    from tests.conftest import VectorLookup


@pytest.mark.parametrize(("label", "key"), list(iter_app_call_vectors()))
def test_example(label: str, key: str, vector_lookup: VectorLookup) -> None:
    assert_example(label, vector_lookup(key))


@pytest.mark.parametrize(("label", "key"), list(iter_app_call_vectors()))
def test_multisig_example(label: str, key: str, vector_lookup: VectorLookup) -> None:
    assert_multisig_example(label, vector_lookup(key))


@pytest.mark.parametrize(("label", "key"), list(iter_app_call_vectors()))
def test_get_transaction_id(label: str, key: str, vector_lookup: VectorLookup) -> None:
    assert_transaction_id(label, vector_lookup(key))


@pytest.mark.parametrize(("label", "key"), list(iter_app_call_vectors()))
def test_assign_fee(label: str, key: str, vector_lookup: VectorLookup) -> None:
    assert_assign_fee(label, vector_lookup(key))


@pytest.mark.parametrize(("label", "key"), list(iter_app_call_vectors()))
def test_get_encoded_transaction_type(label: str, key: str, vector_lookup: VectorLookup) -> None:
    assert_encoded_transaction_type(label, vector_lookup(key))


@pytest.mark.parametrize(("label", "key"), list(iter_app_call_vectors()))
def test_decode_without_prefix(label: str, key: str, vector_lookup: VectorLookup) -> None:
    assert_decode_without_prefix(label, vector_lookup(key))


@pytest.mark.parametrize(("label", "key"), list(iter_app_call_vectors()))
def test_decode_with_prefix(label: str, key: str, vector_lookup: VectorLookup) -> None:
    assert_decode_with_prefix(label, vector_lookup(key))


@pytest.mark.parametrize(("label", "key"), list(iter_app_call_vectors()))
def test_encode_with_auth_address(label: str, key: str, vector_lookup: VectorLookup) -> None:
    assert_encode_with_auth_address(label, vector_lookup(key))


@pytest.mark.parametrize(("label", "key"), list(iter_app_call_vectors()))
def test_encode_with_signature(label: str, key: str, vector_lookup: VectorLookup) -> None:
    assert_encode_with_signature(label, vector_lookup(key))


@pytest.mark.parametrize(("label", "key"), list(iter_app_call_vectors()))
def test_encode(label: str, key: str, vector_lookup: VectorLookup) -> None:
    assert_encode(label, vector_lookup(key))


@pytest.fixture
def app_create_transaction(vector_lookup: VectorLookup) -> Transaction:
    vector = vector_lookup("appCreate")
    return vector.transaction


@pytest.fixture
def base_update_transaction(vector_lookup: VectorLookup) -> Transaction:
    vector = vector_lookup("appUpdate")
    return vector.transaction


@pytest.fixture
def base_call_transaction(vector_lookup: VectorLookup) -> Transaction:
    vector = vector_lookup("appCall")
    return vector.transaction


def test_should_throw_error_when_approval_program_is_missing_for_app_creation(
    app_create_transaction: Transaction,
) -> None:
    tx = clone_transaction(
        app_create_transaction,
        app_call=build_app_call(
            app_id=0,
            on_complete=OnApplicationComplete.NoOp,
            clear_state_program=b"\x01\x02\x03",
        ),
    )

    assert_validation_error(tx, "App call validation failed: Approval program is required")


def test_should_throw_error_when_clear_state_program_is_missing_for_app_creation(
    app_create_transaction: Transaction,
) -> None:
    tx = clone_transaction(
        app_create_transaction,
        app_call=build_app_call(
            app_id=0,
            on_complete=OnApplicationComplete.NoOp,
            approval_program=b"\x01\x02\x03",
        ),
    )

    assert_validation_error(tx, "App call validation failed: Clear state program is required")


def test_should_throw_error_when_extra_program_pages_exceed_maximum(app_create_transaction: Transaction) -> None:
    tx = clone_transaction(
        app_create_transaction,
        app_call=build_app_call(
            app_id=0,
            on_complete=OnApplicationComplete.NoOp,
            approval_program=b"\x01\x02\x03",
            clear_state_program=b"\x04\x05\x06",
            extra_program_pages=4,
        ),
    )

    assert_validation_error(tx, "App call validation failed: Extra program pages cannot exceed 3 pages, got 4")


def test_should_throw_error_when_approval_program_exceeds_max_size(app_create_transaction: Transaction) -> None:
    tx = clone_transaction(
        app_create_transaction,
        app_call=build_app_call(
            app_id=0,
            on_complete=OnApplicationComplete.NoOp,
            approval_program=b"\x00" * 2049,
            clear_state_program=b"\x04\x05\x06",
        ),
    )

    assert_validation_error(tx, "App call validation failed: Approval program cannot exceed 2048 bytes")


def test_should_throw_error_when_clear_state_program_exceeds_max_size(app_create_transaction: Transaction) -> None:
    tx = clone_transaction(
        app_create_transaction,
        app_call=build_app_call(
            app_id=0,
            on_complete=OnApplicationComplete.NoOp,
            approval_program=b"\x01\x02\x03",
            clear_state_program=b"\x00" * 2049,
        ),
    )

    assert_validation_error(tx, "App call validation failed: Clear state program cannot exceed 2048 bytes")


def test_should_throw_error_when_combined_programs_exceed_max_size(app_create_transaction: Transaction) -> None:
    tx = clone_transaction(
        app_create_transaction,
        app_call=build_app_call(
            app_id=0,
            on_complete=OnApplicationComplete.NoOp,
            approval_program=b"\x00" * 1500,
            clear_state_program=b"\xff" * 1500,
        ),
    )

    assert_validation_error(
        tx,
        "App call validation failed: Combined approval and clear state programs cannot exceed 2048 bytes",
    )


def test_should_throw_error_when_global_state_schema_exceeds_maximum_keys(app_create_transaction: Transaction) -> None:
    tx = clone_transaction(
        app_create_transaction,
        app_call=build_app_call(
            app_id=0,
            on_complete=OnApplicationComplete.NoOp,
            approval_program=b"\x01\x02\x03",
            clear_state_program=b"\x04\x05\x06",
            global_state_schema=StateSchema(num_uints=32, num_byte_slices=33),
        ),
    )

    assert_validation_error(tx, "App call validation failed: Global state schema cannot exceed 64 keys")


def test_should_throw_error_when_local_state_schema_exceeds_maximum_keys(app_create_transaction: Transaction) -> None:
    tx = clone_transaction(
        app_create_transaction,
        app_call=build_app_call(
            app_id=0,
            on_complete=OnApplicationComplete.NoOp,
            approval_program=b"\x01\x02\x03",
            clear_state_program=b"\x04\x05\x06",
            local_state_schema=StateSchema(num_uints=8, num_byte_slices=9),
        ),
    )

    assert_validation_error(tx, "App call validation failed: Local state schema cannot exceed 16 keys")


def test_should_validate_valid_app_creation_transaction(app_create_transaction: Transaction) -> None:
    tx = clone_transaction(
        app_create_transaction,
        app_call=build_app_call(
            app_id=0,
            on_complete=OnApplicationComplete.NoOp,
            approval_program=b"\x01\x02\x03",
            clear_state_program=b"\x04\x05\x06",
            global_state_schema=StateSchema(num_uints=32, num_byte_slices=32),
            local_state_schema=StateSchema(num_uints=8, num_byte_slices=8),
            extra_program_pages=3,
        ),
    )

    validate_transaction(tx)


def test_should_validate_app_creation_with_large_programs_when_extra_pages_are_provided(
    app_create_transaction: Transaction,
) -> None:
    tx = clone_transaction(
        app_create_transaction,
        app_call=build_app_call(
            app_id=0,
            on_complete=OnApplicationComplete.NoOp,
            approval_program=b"\xaa" * 4000,
            clear_state_program=b"\x04\x05\x06",
            extra_program_pages=2,
        ),
    )

    validate_transaction(tx)


def test_should_throw_error_when_approval_program_is_missing_for_app_update(
    base_update_transaction: Transaction,
) -> None:
    tx = clone_transaction(
        base_update_transaction,
        app_call=build_app_call(
            app_id=123,
            on_complete=OnApplicationComplete.UpdateApplication,
            clear_state_program=b"\x01\x02\x03",
        ),
    )

    assert_validation_error(tx, "App call validation failed: Approval program is required")


def test_should_throw_error_when_clear_state_program_is_missing_for_app_update(
    base_update_transaction: Transaction,
) -> None:
    tx = clone_transaction(
        base_update_transaction,
        app_call=build_app_call(
            app_id=123,
            on_complete=OnApplicationComplete.UpdateApplication,
            approval_program=b"\x01\x02\x03",
        ),
    )

    assert_validation_error(tx, "App call validation failed: Clear state program is required")


def test_should_throw_error_when_trying_to_modify_global_state_schema(base_update_transaction: Transaction) -> None:
    tx = clone_transaction(
        base_update_transaction,
        app_call=build_app_call(
            app_id=123,
            on_complete=OnApplicationComplete.UpdateApplication,
            approval_program=b"\x01",
            clear_state_program=b"\x02",
            global_state_schema=StateSchema(num_uints=1, num_byte_slices=1),
        ),
    )

    assert_validation_error(tx, "App call validation failed: Global state schema is immutable and cannot be changed")


def test_should_throw_error_when_trying_to_modify_local_state_schema(base_update_transaction: Transaction) -> None:
    tx = clone_transaction(
        base_update_transaction,
        app_call=build_app_call(
            app_id=123,
            on_complete=OnApplicationComplete.UpdateApplication,
            approval_program=b"\x01",
            clear_state_program=b"\x02",
            local_state_schema=StateSchema(num_uints=1, num_byte_slices=1),
        ),
    )

    assert_validation_error(tx, "App call validation failed: Local state schema is immutable and cannot be changed")


def test_should_throw_error_when_trying_to_modify_extra_program_pages(base_update_transaction: Transaction) -> None:
    tx = clone_transaction(
        base_update_transaction,
        app_call=build_app_call(
            app_id=123,
            on_complete=OnApplicationComplete.UpdateApplication,
            approval_program=b"\x01",
            clear_state_program=b"\x02",
            extra_program_pages=1,
        ),
    )

    assert_validation_error(tx, "App call validation failed: Extra program pages is immutable and cannot be changed")


def test_should_validate_valid_app_update_transaction(base_update_transaction: Transaction) -> None:
    tx = clone_transaction(
        base_update_transaction,
        app_call=build_app_call(
            app_id=123,
            on_complete=OnApplicationComplete.UpdateApplication,
            approval_program=b"\x01",
            clear_state_program=b"\x02",
        ),
    )

    validate_transaction(tx)


def test_should_validate_valid_app_call_transaction(base_call_transaction: Transaction) -> None:
    tx = clone_transaction(
        base_call_transaction,
        app_call=build_app_call(
            app_id=123,
            on_complete=OnApplicationComplete.NoOp,
            args=(b"\x01\x02\x03", b"\x04\x05\x06"),
            account_references=("ADSFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFKJSDFK",),
            app_references=(456, 789),
            asset_references=(101112, 131415),
        ),
    )

    validate_transaction(tx)


@pytest.mark.parametrize(
    "on_complete",
    [
        OnApplicationComplete.DeleteApplication,
        OnApplicationComplete.OptIn,
        OnApplicationComplete.CloseOut,
        OnApplicationComplete.ClearState,
    ],
)
def test_should_validate_other_app_operations(
    base_call_transaction: Transaction, on_complete: OnApplicationComplete
) -> None:
    tx = clone_transaction(
        base_call_transaction,
        app_call=build_app_call(app_id=123, on_complete=on_complete),
    )

    validate_transaction(tx)


def test_should_throw_error_when_too_many_args_are_provided(base_call_transaction: Transaction) -> None:
    args = tuple(bytes([i]) for i in range(17))
    tx = clone_transaction(
        base_call_transaction,
        app_call=build_app_call(app_id=123, on_complete=OnApplicationComplete.NoOp, args=args),
    )

    assert_validation_error(tx, "App call validation failed: Args cannot exceed 16 arguments")


def test_should_throw_error_when_args_total_size_exceeds_maximum(base_call_transaction: Transaction) -> None:
    tx = clone_transaction(
        base_call_transaction,
        app_call=build_app_call(
            app_id=123,
            on_complete=OnApplicationComplete.NoOp,
            args=(b"\x01" * 2049,),
        ),
    )

    assert_validation_error(tx, "App call validation failed: Args total size cannot exceed 2048 bytes")


def test_should_throw_error_when_too_many_account_references_are_provided(base_call_transaction: Transaction) -> None:
    accounts = tuple("A" * 58 for _ in range(5))
    tx = clone_transaction(
        base_call_transaction,
        app_call=build_app_call(app_id=123, on_complete=OnApplicationComplete.NoOp, account_references=accounts),
    )

    assert_validation_error(tx, "App call validation failed: Account references cannot exceed 4 refs")


def test_should_throw_error_when_too_many_app_references_are_provided(base_call_transaction: Transaction) -> None:
    apps = tuple(range(1, 10))
    tx = clone_transaction(
        base_call_transaction,
        app_call=build_app_call(app_id=123, on_complete=OnApplicationComplete.NoOp, app_references=apps),
    )

    assert_validation_error(tx, "App call validation failed: App references cannot exceed 8 refs")


def test_should_throw_error_when_too_many_asset_references_are_provided(base_call_transaction: Transaction) -> None:
    assets = tuple(range(1, 10))
    tx = clone_transaction(
        base_call_transaction,
        app_call=build_app_call(app_id=123, on_complete=OnApplicationComplete.NoOp, asset_references=assets),
    )

    assert_validation_error(tx, "App call validation failed: Asset references cannot exceed 8 refs")


def test_should_throw_error_when_box_references_exceed_limit(base_call_transaction: Transaction) -> None:
    app_call = base_call_transaction.app_call
    assert app_call is not None
    boxes = tuple(BoxReference(app_id=app_call.app_id, name=b"box") for _ in range(9))
    tx = clone_transaction(
        base_call_transaction,
        app_call=build_app_call(
            app_id=app_call.app_id,
            on_complete=OnApplicationComplete.NoOp,
            approval_program=app_call.approval_program,
            clear_state_program=app_call.clear_state_program,
            box_references=boxes,
        ),
    )

    assert_validation_error(tx, "App call validation failed: Box references cannot exceed 8 refs")


def test_box_references_round_trip(base_call_transaction: Transaction) -> None:
    app_call = base_call_transaction.app_call
    assert app_call is not None
    boxes = (
        BoxReference(app_id=app_call.app_id, name=b"self"),
        BoxReference(app_id=1234, name=b"foreign"),
    )
    tx = clone_transaction(
        base_call_transaction,
        app_call=build_app_call(
            app_id=app_call.app_id,
            on_complete=app_call.on_complete,
            approval_program=app_call.approval_program,
            clear_state_program=app_call.clear_state_program,
            app_references=(1234,),
            box_references=boxes,
        ),
    )

    decoded = decode_transaction(encode_transaction(tx))
    assert decoded == tx


def test_box_reference_must_reference_known_app(base_call_transaction: Transaction) -> None:
    app_call = base_call_transaction.app_call
    assert app_call is not None
    tx = clone_transaction(
        base_call_transaction,
        app_call=build_app_call(
            app_id=app_call.app_id,
            on_complete=app_call.on_complete,
            approval_program=app_call.approval_program,
            clear_state_program=app_call.clear_state_program,
            app_references=(1234,),
            box_references=(BoxReference(app_id=9999, name=b"bad"),),
        ),
    )

    assert_validation_error(
        tx,
        "App call validation failed: Box reference for app ID 9999 must reference the current app or an app reference",
    )


def test_should_throw_error_when_total_references_exceed_limit(base_call_transaction: Transaction) -> None:
    tx = clone_transaction(
        base_call_transaction,
        app_call=build_app_call(
            app_id=123,
            on_complete=OnApplicationComplete.NoOp,
            account_references=("A" * 58,) * 2,
            app_references=(1, 2, 3),
            asset_references=(4, 5, 6, 7),
        ),
    )

    assert_validation_error(tx, "App call validation failed: Total references cannot exceed 8 refs")


def test_should_validate_app_call_with_maximum_allowed_references(base_call_transaction: Transaction) -> None:
    tx = clone_transaction(
        base_call_transaction,
        app_call=build_app_call(
            app_id=123,
            on_complete=OnApplicationComplete.NoOp,
            args=tuple(bytes([i]) for i in range(16)),
            account_references=("NY6DHEEFW73R2NUWY562U2NNKSKBKVYY5OOQFLD3M2II5RUNKRZDEGUGEA",) * 2,
            app_references=(1, 2, 3),
            asset_references=(4, 5, 6),
        ),
    )

    validate_transaction(tx)
