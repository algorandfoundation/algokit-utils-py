from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum

from algokit_common.constants import (
    MAX_ACCOUNT_REFERENCES,
    MAX_APP_ARGS,
    MAX_APP_REFERENCES,
    MAX_ARGS_SIZE,
    MAX_ASSET_DECIMALS,
    MAX_ASSET_NAME_LENGTH,
    MAX_ASSET_REFERENCES,
    MAX_ASSET_UNIT_NAME_LENGTH,
    MAX_ASSET_URL_LENGTH,
    MAX_BOX_REFERENCES,
    MAX_EXTRA_PROGRAM_PAGES,
    MAX_GLOBAL_STATE_KEYS,
    MAX_LOCAL_STATE_KEYS,
    MAX_OVERALL_REFERENCES,
    PROGRAM_PAGE_SIZE,
    SIGNATURE_BYTE_LENGTH,
)
from algokit_transact.exceptions import TransactionValidationError
from algokit_transact.models.app_call import AppCallTransactionFields
from algokit_transact.models.asset_config import AssetConfigTransactionFields
from algokit_transact.models.asset_freeze import AssetFreezeTransactionFields
from algokit_transact.models.asset_transfer import AssetTransferTransactionFields
from algokit_transact.models.common import OnApplicationComplete
from algokit_transact.models.key_registration import KeyRegistrationTransactionFields
from algokit_transact.models.signed_transaction import SignedTransaction
from algokit_transact.models.transaction import Transaction


class ValidationIssueCode(Enum):
    REQUIRED_FIELD = "required_field"
    FIELD_TOO_LONG = "field_too_long"
    IMMUTABLE_FIELD = "immutable_field"
    ZERO_VALUE_FIELD = "zero_value_field"
    ARBITRARY_CONSTRAINT = "arbitrary_constraint"


@dataclass(slots=True, frozen=True)
class ValidationIssue:
    code: ValidationIssueCode
    message: str
    field: str | None = None
    context: Mapping[str, object] | None = None


def _issue(
    code: ValidationIssueCode,
    message: str,
    *,
    field: str | None = None,
    context: Mapping[str, object] | None = None,
) -> ValidationIssue:
    return ValidationIssue(code=code, message=message, field=field, context=context)


def validate_signed_transaction(stx: SignedTransaction) -> None:
    validate_transaction(stx.txn)

    signatures = [s for s in (stx.sig, stx.msig, stx.lsig) if s is not None]

    if len(signatures) > 1:
        raise ValueError("Only one signature type can be set")

    if stx.sig is not None and len(stx.sig) != SIGNATURE_BYTE_LENGTH:
        raise ValueError("Signature must be 64 bytes")


def validate_transaction(transaction: Transaction) -> None:
    if not transaction.sender:
        raise TransactionValidationError("Transaction sender is required")

    type_fields = [
        transaction.payment,
        transaction.asset_transfer,
        transaction.asset_config,
        transaction.application_call,
        transaction.key_registration,
        transaction.asset_freeze,
        transaction.heartbeat,
        transaction.state_proof,
    ]
    match sum(1 for f in type_fields if f is not None):
        case 0:
            raise TransactionValidationError("No transaction type specific field is set")
        case n if n > 1:
            raise TransactionValidationError("Multiple transaction type specific fields set")

    issues: list[ValidationIssue] = []
    type_label: str | None = None

    match transaction:
        case Transaction(application_call=app_call) if app_call is not None:
            issues.extend(validate_app_call_fields(app_call))
            type_label = "App call"
        case Transaction(asset_config=asset_config) if asset_config is not None:
            issues.extend(validate_asset_config_fields(asset_config))
            type_label = "Asset config"
        case Transaction(asset_transfer=asset_transfer) if asset_transfer is not None:
            issues.extend(validate_asset_transfer_fields(asset_transfer))
            type_label = "Asset transfer"
        case Transaction(asset_freeze=asset_freeze) if asset_freeze is not None:
            issues.extend(validate_asset_freeze_fields(asset_freeze))
            type_label = "Asset freeze"
        case Transaction(key_registration=key_registration) if key_registration is not None:
            issues.extend(validate_key_registration_fields(key_registration))
            type_label = "Key registration"

    if issues and type_label:
        messages = "\n".join(issue.message for issue in issues)
        raise TransactionValidationError(f"{type_label} validation failed: {messages}", issues=issues)


def validate_app_call_fields(app_call: AppCallTransactionFields) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []

    if app_call.app_id == 0:
        issues.extend(_validate_app_creation(app_call))
    else:
        issues.extend(_validate_app_operation(app_call))

    issues.extend(_validate_app_common_fields(app_call))
    return issues


def _validate_app_creation(app_call: AppCallTransactionFields) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    issues.extend(_require_creation_programs(app_call))
    issues.extend(_validate_program_sizes(app_call))
    issues.extend(_validate_state_schema_limits(app_call))
    return issues


def _require_creation_programs(app_call: AppCallTransactionFields) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    match (app_call.approval_program, app_call.clear_state_program):
        case (None | b"", _):
            issues.append(
                _issue(ValidationIssueCode.REQUIRED_FIELD, "Approval program is required", field="Approval program")
            )
        case (_, None | b""):
            issues.append(
                _issue(
                    ValidationIssueCode.REQUIRED_FIELD, "Clear state program is required", field="Clear state program"
                )
            )
    return issues


def _validate_program_sizes(app_call: AppCallTransactionFields) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    extra_pages = app_call.extra_program_pages or 0
    max_program_size = PROGRAM_PAGE_SIZE * (1 + extra_pages)
    approval_size = len(app_call.approval_program or b"")
    clear_state_size = len(app_call.clear_state_program or b"")
    combined_size = approval_size + clear_state_size

    match extra_pages:
        case n if n > MAX_EXTRA_PROGRAM_PAGES:
            issues.append(
                _issue(
                    ValidationIssueCode.FIELD_TOO_LONG,
                    f"Extra program pages cannot exceed {MAX_EXTRA_PROGRAM_PAGES} pages, got {n}",
                    field="Extra program pages",
                    context={"max": MAX_EXTRA_PROGRAM_PAGES, "actual": n, "unit": "pages"},
                )
            )

    match approval_size:
        case size if size > max_program_size:
            issues.append(
                _issue(
                    ValidationIssueCode.FIELD_TOO_LONG,
                    f"Approval program cannot exceed {max_program_size} bytes",
                    field="Approval program",
                    context={"max": max_program_size, "actual": size, "unit": "bytes"},
                )
            )

    match clear_state_size:
        case size if size > max_program_size:
            issues.append(
                _issue(
                    ValidationIssueCode.FIELD_TOO_LONG,
                    f"Clear state program cannot exceed {max_program_size} bytes",
                    field="Clear state program",
                    context={"max": max_program_size, "actual": size, "unit": "bytes"},
                )
            )

    match combined_size:
        case size if size > max_program_size:
            issues.append(
                _issue(
                    ValidationIssueCode.FIELD_TOO_LONG,
                    f"Combined approval and clear state programs cannot exceed {max_program_size} bytes",
                    field="Combined program size",
                    context={"max": max_program_size, "actual": size, "unit": "bytes"},
                )
            )

    return issues


def _validate_state_schema_limits(app_call: AppCallTransactionFields) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if app_call.global_state_schema is not None:
        total = app_call.global_state_schema.num_uints + app_call.global_state_schema.num_byte_slices
        if total > MAX_GLOBAL_STATE_KEYS:
            issues.append(
                _issue(
                    ValidationIssueCode.FIELD_TOO_LONG,
                    f"Global state schema cannot exceed {MAX_GLOBAL_STATE_KEYS} keys",
                    field="Global state schema",
                    context={"max": MAX_GLOBAL_STATE_KEYS, "actual": total, "unit": "keys"},
                )
            )

    if app_call.local_state_schema is not None:
        total = app_call.local_state_schema.num_uints + app_call.local_state_schema.num_byte_slices
        if total > MAX_LOCAL_STATE_KEYS:
            issues.append(
                _issue(
                    ValidationIssueCode.FIELD_TOO_LONG,
                    f"Local state schema cannot exceed {MAX_LOCAL_STATE_KEYS} keys",
                    field="Local state schema",
                    context={"max": MAX_LOCAL_STATE_KEYS, "actual": total, "unit": "keys"},
                )
            )

    return issues


def _validate_app_operation(app_call: AppCallTransactionFields) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []

    def immutable(field: str) -> None:
        issues.append(
            _issue(ValidationIssueCode.IMMUTABLE_FIELD, f"{field} is immutable and cannot be changed", field=field)
        )

    match app_call.on_complete:
        case OnApplicationComplete.UpdateApplication:
            if not app_call.approval_program:
                issues.append(
                    _issue(ValidationIssueCode.REQUIRED_FIELD, "Approval program is required", field="Approval program")
                )
            if not app_call.clear_state_program:
                issues.append(
                    _issue(
                        ValidationIssueCode.REQUIRED_FIELD,
                        "Clear state program is required",
                        field="Clear state program",
                    )
                )

    if app_call.global_state_schema is not None:
        immutable("Global state schema")
    if app_call.local_state_schema is not None:
        immutable("Local state schema")
    if app_call.extra_program_pages is not None:
        immutable("Extra program pages")

    return issues


def _validate_app_common_fields(app_call: AppCallTransactionFields) -> list[ValidationIssue]:
    return [
        *_validate_app_args_limits(app_call),
        *_validate_reference_limits(app_call),
        *_validate_box_reference_constraints(app_call),
        *_validate_total_reference_limit(app_call),
    ]


def _validate_app_args_limits(app_call: AppCallTransactionFields) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if app_call.args is None:
        return issues
    if len(app_call.args) > MAX_APP_ARGS:
        issues.append(
            _issue(
                ValidationIssueCode.FIELD_TOO_LONG,
                f"Args cannot exceed {MAX_APP_ARGS} arguments",
                field="Args",
                context={"max": MAX_APP_ARGS, "actual": len(app_call.args), "unit": "arguments"},
            )
        )
    total_size = sum(len(arg) for arg in app_call.args)
    if total_size > MAX_ARGS_SIZE:
        issues.append(
            _issue(
                ValidationIssueCode.FIELD_TOO_LONG,
                f"Args total size cannot exceed {MAX_ARGS_SIZE} bytes",
                field="Args total size",
                context={"max": MAX_ARGS_SIZE, "actual": total_size, "unit": "bytes"},
            )
        )
    return issues


def _validate_reference_limits(app_call: AppCallTransactionFields) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    reference_limits = (
        ("Account references", app_call.account_references, MAX_ACCOUNT_REFERENCES),
        ("App references", app_call.app_references, MAX_APP_REFERENCES),
        ("Asset references", app_call.asset_references, MAX_ASSET_REFERENCES),
    )
    for label, refs, limit in reference_limits:
        if refs is not None and len(refs) > limit:
            issues.append(
                _issue(
                    ValidationIssueCode.FIELD_TOO_LONG,
                    f"{label} cannot exceed {limit} refs",
                    field=label,
                    context={"max": limit, "actual": len(refs), "unit": "refs"},
                )
            )

    return issues


def _validate_box_reference_constraints(app_call: AppCallTransactionFields) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    box_refs = app_call.box_references or ()
    if not box_refs:
        return issues
    if len(box_refs) > MAX_BOX_REFERENCES:
        issues.append(
            _issue(
                ValidationIssueCode.FIELD_TOO_LONG,
                f"Box references cannot exceed {MAX_BOX_REFERENCES} refs",
                field="Box references",
                context={"max": MAX_BOX_REFERENCES, "actual": len(box_refs), "unit": "refs"},
            )
        )
    allowed_app_ids: set[int] = {app_call.app_id, 0}
    allowed_app_ids.update(app_call.app_references or ())
    for ref in box_refs:
        if ref.app_id not in allowed_app_ids:
            issues.append(
                _issue(
                    ValidationIssueCode.ARBITRARY_CONSTRAINT,
                    f"Box reference for app ID {ref.app_id} must reference the current app or an app reference",
                    field="Box references",
                )
            )
    return issues


def _validate_total_reference_limit(app_call: AppCallTransactionFields) -> list[ValidationIssue]:
    total_refs = (
        len(app_call.account_references or ())
        + len(app_call.app_references or ())
        + len(app_call.asset_references or ())
        + len(app_call.box_references or ())
    )
    if total_refs <= MAX_OVERALL_REFERENCES:
        return []
    return [
        _issue(
            ValidationIssueCode.FIELD_TOO_LONG,
            f"Total references cannot exceed {MAX_OVERALL_REFERENCES} refs",
            field="Total references",
            context={"max": MAX_OVERALL_REFERENCES, "actual": total_refs, "unit": "refs"},
        )
    ]


def validate_asset_config_fields(asset_config: AssetConfigTransactionFields) -> list[ValidationIssue]:
    if asset_config.asset_id == 0:
        return _validate_asset_creation(asset_config)
    return _validate_asset_configuration(asset_config)


def _validate_asset_creation(asset_config: AssetConfigTransactionFields) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []

    def check_len(name: str, value: str | None, limit: int) -> None:
        match value:
            case str(s) if len(s) > limit:
                issues.append(
                    _issue(
                        ValidationIssueCode.FIELD_TOO_LONG,
                        f"{name} cannot exceed {limit} bytes, got {len(s)}",
                        field=name,
                        context={"max": limit, "actual": len(s), "unit": "bytes"},
                    )
                )

    match asset_config.total:
        case None:
            issues.append(_issue(ValidationIssueCode.REQUIRED_FIELD, "Total is required", field="Total"))

    match asset_config.decimals:
        case int(d) if d > MAX_ASSET_DECIMALS:
            issues.append(
                _issue(
                    ValidationIssueCode.FIELD_TOO_LONG,
                    f"Decimals cannot exceed {MAX_ASSET_DECIMALS} decimal places, got {d}",
                    field="Decimals",
                    context={"max": MAX_ASSET_DECIMALS, "actual": d, "unit": "decimal places"},
                )
            )

    check_len("Unit name", asset_config.unit_name, MAX_ASSET_UNIT_NAME_LENGTH)
    check_len("Asset name", asset_config.asset_name, MAX_ASSET_NAME_LENGTH)
    check_len("Url", asset_config.url, MAX_ASSET_URL_LENGTH)

    return issues


def _validate_asset_configuration(asset_config: AssetConfigTransactionFields) -> list[ValidationIssue]:
    immutable_fields = [
        ("total", "Total"),
        ("decimals", "Decimals"),
        ("default_frozen", "Default frozen"),
        ("asset_name", "Asset name"),
        ("unit_name", "Unit name"),
        ("url", "Url"),
        ("metadata_hash", "Metadata hash"),
    ]

    return [
        _issue(
            ValidationIssueCode.IMMUTABLE_FIELD,
            f"{label} is immutable and cannot be changed",
            field=label,
        )
        for attr, label in immutable_fields
        if getattr(asset_config, attr) is not None
    ]


def validate_asset_transfer_fields(asset_transfer: AssetTransferTransactionFields) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []

    if asset_transfer.asset_id == 0:
        issues.append(
            _issue(
                ValidationIssueCode.ZERO_VALUE_FIELD,
                "Asset ID must not be 0",
                field="Asset ID",
            )
        )

    return issues


def validate_asset_freeze_fields(asset_freeze: AssetFreezeTransactionFields) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []

    if asset_freeze.asset_id == 0:
        issues.append(
            _issue(
                ValidationIssueCode.ZERO_VALUE_FIELD,
                "Asset ID must not be 0",
                field="Asset ID",
            )
        )

    return issues


def validate_key_registration_fields(key_reg: KeyRegistrationTransactionFields) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []

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
        return issues

    required_fields = [
        (key_reg.vote_key, "Vote key"),
        (key_reg.selection_key, "Selection key"),
        (key_reg.state_proof_key, "State proof key"),
        (key_reg.vote_first, "Vote first"),
        (key_reg.vote_last, "Vote last"),
        (key_reg.vote_key_dilution, "Vote key dilution"),
    ]

    for value, field_name in required_fields:
        if value is None:
            issues.append(_issue(ValidationIssueCode.REQUIRED_FIELD, f"{field_name} is required", field=field_name))

    if key_reg.vote_first is not None and key_reg.vote_last is not None and key_reg.vote_first >= key_reg.vote_last:
        issues.append(
            _issue(
                ValidationIssueCode.ARBITRARY_CONSTRAINT,
                "Vote first must be less than vote last",
                field="Vote first",
            )
        )

    if key_reg.non_participation:
        issues.append(
            _issue(
                ValidationIssueCode.ARBITRARY_CONSTRAINT,
                "Online key registration cannot have non participation flag set",
                field="Non participation",
            )
        )

    return issues
