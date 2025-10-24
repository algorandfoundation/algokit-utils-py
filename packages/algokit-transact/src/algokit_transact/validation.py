from __future__ import annotations

from .constants import (
    MAX_ACCOUNT_REFERENCES,
    MAX_APP_ARGS,
    MAX_APP_REFERENCES,
    MAX_ARGS_TOTAL_BYTES,
    MAX_ASSET_DECIMALS,
    MAX_ASSET_NAME_LENGTH,
    MAX_ASSET_REFERENCES,
    MAX_ASSET_UNIT_NAME_LENGTH,
    MAX_ASSET_URL_LENGTH,
    MAX_EXTRA_PROGRAM_PAGES,
    MAX_GLOBAL_STATE_KEYS,
    MAX_LOCAL_STATE_KEYS,
    MAX_TOTAL_REFERENCES,
    PROGRAM_PAGE_SIZE,
)
from .errors import TransactionValidationError
from .types import (
    AppCallFields,
    AssetConfigFields,
    AssetFreezeFields,
    AssetTransferFields,
    KeyRegistrationFields,
    OnApplicationComplete,
    Transaction,
)


def validate_transaction(transaction: Transaction) -> None:
    if not transaction.sender:
        raise TransactionValidationError("Transaction sender is required")

    type_fields = [
        transaction.payment,
        transaction.asset_transfer,
        transaction.asset_config,
        transaction.app_call,
        transaction.key_registration,
        transaction.asset_freeze,
        transaction.heartbeat,
        transaction.state_proof,
    ]
    set_count = sum(1 for f in type_fields if f is not None)
    if set_count == 0:
        raise TransactionValidationError("No transaction type specific field is set")
    if set_count > 1:
        raise TransactionValidationError("Multiple transaction type specific fields set")

    errors: list[str] = []
    type_label: str | None = None

    if transaction.app_call is not None:
        errors.extend(_validate_app_call(transaction.app_call))
        type_label = "App call"
    elif transaction.asset_config is not None:
        errors.extend(_validate_asset_config(transaction.asset_config))
        type_label = "Asset config"
    elif transaction.asset_transfer is not None:
        errors.extend(_validate_asset_transfer(transaction.asset_transfer))
        type_label = "Asset transfer"
    elif transaction.asset_freeze is not None:
        errors.extend(_validate_asset_freeze(transaction.asset_freeze))
        type_label = "Asset freeze"
    elif transaction.key_registration is not None:
        errors.extend(_validate_key_registration(transaction.key_registration))
        type_label = "Key registration"

    if errors and type_label is not None:
        raise TransactionValidationError(f"{type_label} validation failed: " + "\n".join(errors))


def _validate_app_call(app_call: AppCallFields) -> list[str]:
    errors: list[str] = []

    if app_call.app_id == 0:
        errors.extend(_validate_app_creation(app_call))
    else:
        errors.extend(_validate_app_operation(app_call))

    errors.extend(_validate_app_common_fields(app_call))
    return errors


def _validate_app_creation(app_call: AppCallFields) -> list[str]:  # noqa: C901
    errors: list[str] = []

    if not app_call.approval_program:
        errors.append("Approval program is required")
    if not app_call.clear_state_program:
        errors.append("Clear state program is required")

    extra_pages = app_call.extra_program_pages or 0
    if extra_pages > MAX_EXTRA_PROGRAM_PAGES:
        errors.append(f"Extra program pages cannot exceed {MAX_EXTRA_PROGRAM_PAGES} pages, got {extra_pages}")

    max_program_size = PROGRAM_PAGE_SIZE * (1 + extra_pages)

    approval_size = len(app_call.approval_program or b"")
    clear_state_size = len(app_call.clear_state_program or b"")

    if approval_size > max_program_size:
        errors.append(f"Approval program cannot exceed {max_program_size} bytes")
    if clear_state_size > max_program_size:
        errors.append(f"Clear state program cannot exceed {max_program_size} bytes")

    if approval_size + clear_state_size > max_program_size:
        errors.append(f"Combined approval and clear state programs cannot exceed {max_program_size} bytes")

    if app_call.global_state_schema is not None:
        total = app_call.global_state_schema.num_uints + app_call.global_state_schema.num_byte_slices
        if total > MAX_GLOBAL_STATE_KEYS:
            errors.append(f"Global state schema cannot exceed {MAX_GLOBAL_STATE_KEYS} keys")

    if app_call.local_state_schema is not None:
        total = app_call.local_state_schema.num_uints + app_call.local_state_schema.num_byte_slices
        if total > MAX_LOCAL_STATE_KEYS:
            errors.append(f"Local state schema cannot exceed {MAX_LOCAL_STATE_KEYS} keys")

    return errors


def _validate_app_operation(app_call: AppCallFields) -> list[str]:
    errors: list[str] = []

    if app_call.on_complete is OnApplicationComplete.UpdateApplication:
        if not app_call.approval_program:
            errors.append("Approval program is required")
        if not app_call.clear_state_program:
            errors.append("Clear state program is required")

    if app_call.global_state_schema is not None:
        errors.append("Global state schema is immutable and cannot be changed")
    if app_call.local_state_schema is not None:
        errors.append("Local state schema is immutable and cannot be changed")
    if app_call.extra_program_pages is not None:
        errors.append("Extra program pages is immutable and cannot be changed")

    return errors


def _validate_app_common_fields(app_call: AppCallFields) -> list[str]:
    errors: list[str] = []

    if app_call.args is not None:
        if len(app_call.args) > MAX_APP_ARGS:
            errors.append(f"Args cannot exceed {MAX_APP_ARGS} arguments")
        total_size = sum(len(arg) for arg in app_call.args)
        if total_size > MAX_ARGS_TOTAL_BYTES:
            errors.append(f"Args total size cannot exceed {MAX_ARGS_TOTAL_BYTES} bytes")

    if app_call.account_references is not None and len(app_call.account_references) > MAX_ACCOUNT_REFERENCES:
        errors.append(f"Account references cannot exceed {MAX_ACCOUNT_REFERENCES} refs")

    if app_call.app_references is not None and len(app_call.app_references) > MAX_APP_REFERENCES:
        errors.append(f"App references cannot exceed {MAX_APP_REFERENCES} refs")

    if app_call.asset_references is not None and len(app_call.asset_references) > MAX_ASSET_REFERENCES:
        errors.append(f"Asset references cannot exceed {MAX_ASSET_REFERENCES} refs")

    total_refs = (
        len(app_call.account_references or ())
        + len(app_call.app_references or ())
        + len(app_call.asset_references or ())
    )

    if total_refs > MAX_TOTAL_REFERENCES:
        errors.append(f"Total references cannot exceed {MAX_TOTAL_REFERENCES} refs")

    return errors


def _validate_asset_config(asset_config: AssetConfigFields) -> list[str]:
    if asset_config.asset_id == 0:
        return _validate_asset_creation(asset_config)
    return _validate_asset_configuration(asset_config)


def _validate_asset_creation(asset_config: AssetConfigFields) -> list[str]:
    errors: list[str] = []

    if asset_config.total is None:
        errors.append("Total is required")

    if asset_config.decimals is not None and asset_config.decimals > MAX_ASSET_DECIMALS:
        errors.append(f"Decimals cannot exceed {MAX_ASSET_DECIMALS} decimal places, got {asset_config.decimals}")

    if asset_config.unit_name and len(asset_config.unit_name) > MAX_ASSET_UNIT_NAME_LENGTH:
        errors.append(f"Unit name cannot exceed {MAX_ASSET_UNIT_NAME_LENGTH} bytes, got {len(asset_config.unit_name)}")

    if asset_config.asset_name and len(asset_config.asset_name) > MAX_ASSET_NAME_LENGTH:
        errors.append(f"Asset name cannot exceed {MAX_ASSET_NAME_LENGTH} bytes, got {len(asset_config.asset_name)}")

    if asset_config.url and len(asset_config.url) > MAX_ASSET_URL_LENGTH:
        errors.append("Url cannot exceed 96 bytes")

    return errors


def _validate_asset_configuration(asset_config: AssetConfigFields) -> list[str]:
    errors: list[str] = []

    def _add_immutable(field: str) -> None:
        errors.append(f"{field} is immutable and cannot be changed")

    if asset_config.total is not None:
        _add_immutable("Total")
    if asset_config.decimals is not None:
        _add_immutable("Decimals")
    if asset_config.default_frozen is not None:
        _add_immutable("Default frozen")
    if asset_config.asset_name is not None:
        _add_immutable("Asset name")
    if asset_config.unit_name is not None:
        _add_immutable("Unit name")
    if asset_config.url is not None:
        _add_immutable("Url")
    if asset_config.metadata_hash is not None:
        _add_immutable("Metadata hash")

    return errors


def _validate_asset_transfer(asset_transfer: AssetTransferFields) -> list[str]:
    errors: list[str] = []

    if asset_transfer.asset_id == 0:
        errors.append("Asset ID must not be 0")

    return errors


def _validate_asset_freeze(asset_freeze: AssetFreezeFields) -> list[str]:
    errors: list[str] = []

    if asset_freeze.asset_id == 0:
        errors.append("Asset ID must not be 0")

    return errors


def _validate_key_registration(key_reg: KeyRegistrationFields) -> list[str]:
    errors: list[str] = []

    has_participation_fields = any(
        field is not None
        for field in (
            key_reg.vote_key,
            key_reg.selection_key,
            key_reg.state_proof_key,
            key_reg.vote_first,
            key_reg.vote_last,
            key_reg.vote_key_dilution,
        )
    )

    if not has_participation_fields:
        return errors

    if key_reg.vote_key is None:
        errors.append("Vote key is required")
    if key_reg.selection_key is None:
        errors.append("Selection key is required")
    if key_reg.state_proof_key is None:
        errors.append("State proof key is required")
    if key_reg.vote_first is None:
        errors.append("Vote first is required")
    if key_reg.vote_last is None:
        errors.append("Vote last is required")
    if key_reg.vote_first is not None and key_reg.vote_last is not None and key_reg.vote_first >= key_reg.vote_last:
        errors.append("Vote first must be less than vote last")
    if key_reg.vote_key_dilution is None:
        errors.append("Vote key dilution is required")
    if key_reg.non_participation:
        errors.append("Online key registration cannot have non participation flag set")

    return errors
