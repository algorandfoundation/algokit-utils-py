from collections.abc import Sequence
from dataclasses import dataclass

from typing_extensions import assert_never, assert_type

from algokit_abi import abi, arc56
from algokit_transact.models.app_call import AppCallTransactionFields
from algokit_transact.models.common import OnApplicationComplete, StateSchema
from algokit_transact.models.transaction import TransactionType
from algokit_utils.applications.app_manager import AppManager
from algokit_utils.transactions.builders.app import _compile_program, _convert_box_references
from algokit_utils.transactions.builders.common import (
    BuiltTransaction,
    SuggestedParamsLike,
    TransactionHeader,
    apply_transaction_fees,
    build_transaction,
    build_transaction_header,
)
from algokit_utils.transactions.helpers import calculate_extra_program_pages
from algokit_utils.transactions.types import (
    AppCallMethodCallParams,
    AppCreateMethodCallParams,
    AppDeleteMethodCallParams,
    AppUpdateMethodCallParams,
)

_ARGS_TUPLE_PACKING_THRESHOLD = 15

__all__ = [
    "build_app_call_method_call_transaction",
    "build_app_create_method_call_transaction",
    "build_app_delete_method_call_transaction",
    "build_app_update_method_call_transaction",
]


def build_app_call_method_call_transaction(
    params: AppCallMethodCallParams | AppDeleteMethodCallParams,
    suggested_params: SuggestedParamsLike,
    *,
    method_args: Sequence | None,
    app_manager: AppManager,
    default_validity_window: int,
    default_validity_window_is_explicit: bool,
    is_localnet: bool,
) -> BuiltTransaction:
    header, fee_config = build_transaction_header(
        params,
        suggested_params,
        default_validity_window=default_validity_window,
        default_validity_window_is_explicit=default_validity_window_is_explicit,
        is_localnet=is_localnet,
    )
    common = _build_method_call_common(
        params.app_id,
        params.method,
        method_args,
        header,
        params.account_references,
        params.app_references,
        params.asset_references,
    )
    fields = AppCallTransactionFields(
        app_id=params.app_id,
        on_complete=params.on_complete or OnApplicationComplete.NoOp,
        args=common.args,
        account_references=_to_maybe_list(common.account_references),
        app_references=_to_maybe_list(common.app_references),
        asset_references=_to_maybe_list(common.asset_references),
        box_references=_convert_box_references(params.box_references, app_manager),
    )
    txn = build_transaction(TransactionType.AppCall, header, application_call=fields)
    return apply_transaction_fees(txn, params, fee_config)


def build_app_delete_method_call_transaction(
    params: AppDeleteMethodCallParams,
    suggested_params: SuggestedParamsLike,
    *,
    method_args: Sequence | None,
    app_manager: AppManager,
    default_validity_window: int,
    default_validity_window_is_explicit: bool,
    is_localnet: bool,
) -> BuiltTransaction:
    return build_app_call_method_call_transaction(
        params,
        suggested_params,
        method_args=method_args,
        app_manager=app_manager,
        default_validity_window=default_validity_window,
        default_validity_window_is_explicit=default_validity_window_is_explicit,
        is_localnet=is_localnet,
    )


def build_app_create_method_call_transaction(
    params: AppCreateMethodCallParams,
    suggested_params: SuggestedParamsLike,
    *,
    method_args: Sequence | None,
    app_manager: AppManager,
    default_validity_window: int,
    default_validity_window_is_explicit: bool,
    is_localnet: bool,
) -> BuiltTransaction:
    header, fee_config = build_transaction_header(
        params,
        suggested_params,
        default_validity_window=default_validity_window,
        default_validity_window_is_explicit=default_validity_window_is_explicit,
        is_localnet=is_localnet,
    )
    approval_program = _compile_program(app_manager, params.approval_program)
    clear_state_program = _compile_program(app_manager, params.clear_state_program)
    schema = params.schema
    global_schema = StateSchema(
        num_uints=schema["global_ints"] if schema else 0,
        num_byte_slices=schema["global_byte_slices"] if schema else 0,
    )
    local_schema = StateSchema(
        num_uints=schema["local_ints"] if schema else 0,
        num_byte_slices=schema["local_byte_slices"] if schema else 0,
    )
    extra_pages = params.extra_program_pages or calculate_extra_program_pages(approval_program, clear_state_program)
    common = _build_method_call_common(
        0,
        params.method,
        method_args,
        header,
        params.account_references,
        params.app_references,
        params.asset_references,
    )
    fields = AppCallTransactionFields(
        app_id=0,
        on_complete=params.on_complete or OnApplicationComplete.NoOp,
        approval_program=approval_program,
        clear_state_program=clear_state_program,
        global_state_schema=global_schema,
        local_state_schema=local_schema,
        extra_program_pages=extra_pages,
        args=common.args,
        account_references=_to_maybe_list(common.account_references),
        app_references=_to_maybe_list(common.app_references),
        asset_references=_to_maybe_list(common.asset_references),
        box_references=_convert_box_references(params.box_references, app_manager),
    )
    txn = build_transaction(TransactionType.AppCall, header, application_call=fields)
    return apply_transaction_fees(txn, params, fee_config)


def build_app_update_method_call_transaction(
    params: AppUpdateMethodCallParams,
    suggested_params: SuggestedParamsLike,
    *,
    method_args: Sequence | None,
    app_manager: AppManager,
    default_validity_window: int,
    default_validity_window_is_explicit: bool,
    is_localnet: bool,
) -> BuiltTransaction:
    header, fee_config = build_transaction_header(
        params,
        suggested_params,
        default_validity_window=default_validity_window,
        default_validity_window_is_explicit=default_validity_window_is_explicit,
        is_localnet=is_localnet,
    )
    approval_program = _compile_program(app_manager, params.approval_program)
    clear_state_program = _compile_program(app_manager, params.clear_state_program)
    common = _build_method_call_common(
        params.app_id,
        params.method,
        method_args,
        header,
        params.account_references,
        params.app_references,
        params.asset_references,
    )
    fields = AppCallTransactionFields(
        app_id=params.app_id,
        on_complete=OnApplicationComplete.UpdateApplication,
        approval_program=approval_program,
        clear_state_program=clear_state_program,
        args=common.args,
        account_references=_to_maybe_list(common.account_references),
        app_references=_to_maybe_list(common.app_references),
        asset_references=_to_maybe_list(common.asset_references),
        box_references=_convert_box_references(params.box_references, app_manager),
    )
    txn = build_transaction(TransactionType.AppCall, header, application_call=fields)
    return apply_transaction_fees(txn, params, fee_config)


@dataclass(slots=True)
class _MethodCallCommon:
    args: list[bytes]
    account_references: list[str]
    app_references: list[int]
    asset_references: list[int]


def _build_method_call_common(
    app_id: int,
    method: arc56.Method,
    method_args: Sequence | None,
    header: TransactionHeader,
    account_references: Sequence[str] | None,
    app_references: Sequence[int] | None,
    asset_references: Sequence[int] | None,
) -> _MethodCallCommon:
    accounts, apps, assets = _populate_method_args_into_reference_arrays(
        header.sender,
        app_id,
        method,
        method_args or [],
        account_references,
        app_references,
        asset_references,
    )
    encoded_args = _encode_method_arguments(
        method,
        method_args or [],
        header.sender,
        app_id,
        accounts,
        apps,
        assets,
    )
    return _MethodCallCommon(
        args=encoded_args, account_references=accounts, app_references=apps, asset_references=assets
    )


def _populate_method_args_into_reference_arrays(
    sender: str,
    app_id: int,
    method: arc56.Method,
    method_args: Sequence,
    account_references: Sequence[str] | None,
    app_references: Sequence[int] | None,
    asset_references: Sequence[int] | None,
) -> tuple[list[str], list[int], list[int]]:
    accounts = list(account_references or [])
    apps = list(app_references or [])
    assets = list(asset_references or [])

    for arg_value, arg in zip(method_args, method.args, strict=False):
        if arg_value is None:
            continue
        arg_type = arg.type
        if (
            arg_type == arc56.ReferenceType.ACCOUNT
            and isinstance(arg_value, str)
            and arg_value != sender
            and arg_value not in accounts
        ):
            accounts.append(arg_value)
        elif arg_type == arc56.ReferenceType.ASSET and isinstance(arg_value, int) and arg_value not in assets:
            assets.append(arg_value)
        elif (
            arg_type == arc56.ReferenceType.APPLICATION
            and isinstance(arg_value, int)
            and arg_value != app_id
            and arg_value not in apps
        ):
            apps.append(arg_value)
        # Non-reference args do not change reference arrays
    return accounts, apps, assets


def _encode_method_arguments(
    method: arc56.Method,
    method_args: Sequence,
    sender: str,
    app_id: int,
    account_references: Sequence[str],
    app_references: Sequence[int],
    asset_references: Sequence[int],
) -> list[bytes]:
    encoded_args = list[bytes]()
    encoded_args.append(method.selector)

    abi_types = list[abi.ABIType]()
    abi_values = []

    for arg, arg_value in zip(method.args, method_args, strict=False):
        if arg_value is None:
            continue
        arg_type = arg.type
        if isinstance(arg_type, arc56.TransactionType):
            continue
        if isinstance(arg_type, abi.ABIType):
            abi_type = arg_type
            abi_value = arg_value
        else:
            assert_type(arg_type, arc56.ReferenceType)
            index = _calculate_reference_index(
                arg_value,
                arg_type,
                sender,
                app_id,
                account_references,
                app_references,
                asset_references,
            )
            abi_type = abi.UintType(8)
            abi_value = index
        abi_types.append(abi_type)
        abi_values.append(abi_value)

    if len(abi_types) != len(abi_values):
        raise ValueError("Mismatch between ABI argument types and values")

    encoded_args.extend(_encode_args_with_tuple_packing(abi_types, abi_values))
    return encoded_args


def _calculate_reference_index(
    value: str | int,
    reference_type: arc56.ReferenceType,
    sender: str,
    app_id: int,
    account_references: Sequence[str],
    app_references: Sequence[int],
    asset_references: Sequence[int],
) -> int:
    if reference_type == arc56.ReferenceType.ACCOUNT:
        return _calculate_account_reference_index(value, sender, account_references)
    if reference_type == arc56.ReferenceType.ASSET:
        return _calculate_asset_reference_index(value, asset_references)
    if reference_type == arc56.ReferenceType.APPLICATION:
        return _calculate_application_reference_index(value, app_id, app_references)
    assert_never(reference_type)


def _calculate_account_reference_index(value: str | int, sender: str, account_references: Sequence[str]) -> int:
    if not isinstance(value, str):
        raise ValueError("Account reference arguments must be base32 addresses")
    if value == sender:
        return 0
    if value not in account_references:
        raise ValueError(f"Account reference {value} not present in reference array")
    return account_references.index(value) + 1


def _calculate_asset_reference_index(value: str | int, asset_references: Sequence[int]) -> int:
    if not isinstance(value, int):
        raise ValueError("Asset reference arguments must be integers")
    if value not in asset_references:
        raise ValueError(f"Asset reference {value} not present in reference array")
    return asset_references.index(value)


def _calculate_application_reference_index(value: str | int, app_id: int, app_references: Sequence[int]) -> int:
    if not isinstance(value, int):
        raise ValueError("Application reference arguments must be integers")
    if value == app_id:
        return 0
    if value not in app_references:
        raise ValueError(f"Application reference {value} not present in reference array")
    return app_references.index(value) + 1


def _encode_args_with_tuple_packing(abi_types: Sequence[abi.ABIType], abi_values: Sequence) -> list[bytes]:
    type_value_pairs = list(zip(abi_types, abi_values, strict=True))
    if len(type_value_pairs) > _ARGS_TUPLE_PACKING_THRESHOLD:
        # if the threshold has been exceeded then need to leave 1 element at the end
        # for the packed tuple
        split_at = _ARGS_TUPLE_PACKING_THRESHOLD - 1
    else:
        split_at = len(type_value_pairs)
    unpacked_pairs = type_value_pairs[:split_at]
    packed_pairs = type_value_pairs[split_at:]
    encoded = [abi_type.encode(abi_value) for abi_type, abi_value in unpacked_pairs]

    if packed_pairs:
        tuple_type = abi.TupleType([t[0] for t in packed_pairs])
        encoded.append(tuple_type.encode([t[1] for t in packed_pairs]))
    return encoded


def _to_maybe_list(values: Sequence | None) -> list | None:
    return list(values) if values else None
