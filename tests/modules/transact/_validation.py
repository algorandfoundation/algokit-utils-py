from collections.abc import Iterable
from dataclasses import replace
from typing import Any

import pytest

from algokit_transact import (
    AppCallTransactionFields,
    AssetConfigTransactionFields,
    AssetFreezeTransactionFields,
    AssetTransferTransactionFields,
    BoxReference,
    KeyRegistrationTransactionFields,
    OnApplicationComplete,
    ResourceReference,
    StateSchema,
    Transaction,
    TransactionValidationError,
    validate_transaction,
)


def clone_transaction(transaction: Transaction, **overrides: Any) -> Transaction:
    return replace(transaction, **overrides)


def build_app_call(  # noqa: PLR0913
    *,
    app_id: int,
    on_complete: OnApplicationComplete,
    approval_program: bytes | None = None,
    clear_state_program: bytes | None = None,
    global_state_schema: StateSchema | None = None,
    local_state_schema: StateSchema | None = None,
    args: Iterable[bytes] | None = None,
    account_references: Iterable[str] | None = None,
    app_references: Iterable[int] | None = None,
    asset_references: Iterable[int] | None = None,
    extra_program_pages: int | None = None,
    box_references: Iterable[BoxReference] | None = None,
    access_references: Iterable[ResourceReference] | None = None,
) -> AppCallTransactionFields:
    return AppCallTransactionFields(
        app_id=app_id,
        on_complete=on_complete,
        approval_program=approval_program,
        clear_state_program=clear_state_program,
        global_state_schema=global_state_schema,
        local_state_schema=local_state_schema,
        args=tuple(args) if args is not None else None,
        account_references=tuple(account_references) if account_references is not None else None,
        app_references=tuple(app_references) if app_references is not None else None,
        asset_references=tuple(asset_references) if asset_references is not None else None,
        extra_program_pages=extra_program_pages,
        box_references=tuple(box_references) if box_references is not None else None,
        access_references=tuple(access_references) if access_references is not None else None,
    )


def build_asset_config(  # noqa: PLR0913
    *,
    asset_id: int,
    total: int | None = None,
    decimals: int | None = None,
    default_frozen: bool | None = None,
    asset_name: str | None = None,
    unit_name: str | None = None,
    url: str | None = None,
    metadata_hash: bytes | None = None,
    manager: str | None = None,
    reserve: str | None = None,
    freeze: str | None = None,
    clawback: str | None = None,
) -> AssetConfigTransactionFields:
    return AssetConfigTransactionFields(
        asset_id=asset_id,
        total=total,
        decimals=decimals,
        default_frozen=default_frozen,
        asset_name=asset_name,
        unit_name=unit_name,
        url=url,
        metadata_hash=metadata_hash,
        manager=manager,
        reserve=reserve,
        freeze=freeze,
        clawback=clawback,
    )


def build_asset_transfer(
    *,
    asset_id: int,
    amount: int,
    receiver: str,
    asset_sender: str | None = None,
    close_remainder_to: str | None = None,
) -> AssetTransferTransactionFields:
    return AssetTransferTransactionFields(
        asset_id=asset_id,
        amount=amount,
        receiver=receiver,
        asset_sender=asset_sender,
        close_remainder_to=close_remainder_to,
    )


def build_asset_freeze(
    *,
    asset_id: int,
    freeze_target: str,
    frozen: bool,
) -> AssetFreezeTransactionFields:
    return AssetFreezeTransactionFields(asset_id=asset_id, freeze_target=freeze_target, frozen=frozen)


def build_key_registration(
    *,
    vote_key: bytes | None = None,
    selection_key: bytes | None = None,
    state_proof_key: bytes | None = None,
    vote_first: int | None = None,
    vote_last: int | None = None,
    vote_key_dilution: int | None = None,
    non_participation: bool | None = None,
) -> KeyRegistrationTransactionFields:
    return KeyRegistrationTransactionFields(
        vote_key=vote_key,
        selection_key=selection_key,
        state_proof_key=state_proof_key,
        vote_first=vote_first,
        vote_last=vote_last,
        vote_key_dilution=vote_key_dilution,
        non_participation=non_participation,
    )


def assert_validation_error(transaction: Transaction, message: str) -> None:
    with pytest.raises(TransactionValidationError) as exc:
        validate_transaction(transaction)
    assert message in str(exc.value)
