from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import TypeAlias

import algokit_algosdk as algosdk
import algokit_abi
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

abi = algosdk.abi
ABIReferenceType: TypeAlias = abi.ABIReferenceType
ABIType: TypeAlias = abi.ABIType
Method: TypeAlias = abi.Method
TupleType: TypeAlias = abi.TupleType
UintType: TypeAlias = abi.UintType
is_abi_reference_type = abi.is_abi_reference_type
is_abi_transaction_type = abi.is_abi_transaction_type

ARGS_TUPLE_PACKING_THRESHOLD = 14

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
        account_references=_to_tuple(common.account_references),
        app_references=_to_tuple(common.app_references),
        asset_references=_to_tuple(common.asset_references),
        box_references=_convert_box_references(params.box_references, app_manager),
    )
    txn = build_transaction(TransactionType.AppCall, header, app_call=fields)
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
        account_references=_to_tuple(common.account_references),
        app_references=_to_tuple(common.app_references),
        asset_references=_to_tuple(common.asset_references),
        box_references=_convert_box_references(params.box_references, app_manager),
    )
    txn = build_transaction(TransactionType.AppCall, header, app_call=fields)
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
        account_references=_to_tuple(common.account_references),
        app_references=_to_tuple(common.app_references),
        asset_references=_to_tuple(common.asset_references),
        box_references=_convert_box_references(params.box_references, app_manager),
    )
    txn = build_transaction(TransactionType.AppCall, header, app_call=fields)
    return apply_transaction_fees(txn, params, fee_config)


@dataclass(slots=True)
class _MethodCallCommon:
    args: list[bytes]
    account_references: list[str]
    app_references: list[int]
    asset_references: list[int]


def _build_method_call_common(
    app_id: int,
    method: Method,
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
    method: Method,
    method_args: Sequence,
    account_references: Sequence[str] | None,
    app_references: Sequence[int] | None,
    asset_references: Sequence[int] | None,
) -> tuple[list[str], list[int], list[int]]:
    accounts = list(account_references or [])
    apps = list(app_references or [])
    assets = list(asset_references or [])

    for idx, arg in enumerate(method.args):
        arg_value = method_args[idx] if idx < len(method_args) else None
        arg_type = arg.type
        if isinstance(arg_type, str) and is_abi_reference_type(arg_type):
            if arg_value is None:
                continue
            if arg_type == ABIReferenceType.ACCOUNT and isinstance(arg_value, str):
                if arg_value != sender and arg_value not in accounts:
                    accounts.append(arg_value)
            elif arg_type == ABIReferenceType.ASSET and isinstance(arg_value, int):
                if arg_value not in assets:
                    assets.append(arg_value)
            elif (
                arg_type == ABIReferenceType.APPLICATION
                and isinstance(arg_value, int)
                and arg_value != app_id
                and arg_value not in apps
            ):
                apps.append(arg_value)
        # Non-reference args do not change reference arrays
    return accounts, apps, assets


def _encode_method_arguments(
    method: Method,
    method_args: Sequence,
    sender: str,
    app_id: int,
    account_references: Sequence[str],
    app_references: Sequence[int],
    asset_references: Sequence[int],
) -> list[bytes]:
    encoded_args: list[bytes] = []
    encoded_args.append(method.get_selector())

    abi_types: list[ABIType] = []
    abi_values: list = []

    for idx, arg in enumerate(method.args):
        arg_value = method_args[idx] if idx < len(method_args) else None
        arg_type = arg.type
        if isinstance(arg_type, str):
            if is_abi_transaction_type(arg_type):
                continue
            if is_abi_reference_type(arg_type):
                if arg_value is None:
                    continue
                index = _calculate_reference_index(
                    arg_value,
                    arg_type,
                    sender,
                    app_id,
                    account_references,
                    app_references,
                    asset_references,
                )
                abi_types.append(UintType(8))
                abi_values.append(index)
                continue
            # Non-reference strings should be converted into ABI types
            abi_type = abi.ABIType.from_string(arg_type)
        else:
            abi_type = arg_type

        if arg_value is None:
            continue
        abi_types.append(abi_type)
        abi_values.append(arg_value)

    if len(abi_types) != len(abi_values):
        raise ValueError("Mismatch between ABI argument types and values")

    if len(abi_types) > ARGS_TUPLE_PACKING_THRESHOLD:
        encoded_args.extend(_encode_args_with_tuple_packing(abi_types, abi_values))
    else:
        encoded_args.extend(_encode_args_individually(abi_types, abi_values))
    return encoded_args


def _calculate_reference_index(
    value: str | int,
    reference_type: str,
    sender: str,
    app_id: int,
    account_references: Sequence[str],
    app_references: Sequence[int],
    asset_references: Sequence[int],
) -> int:
    match reference_type:
        case ABIReferenceType.ACCOUNT:
            return _calculate_account_reference_index(value, sender, account_references)
        case ABIReferenceType.ASSET:
            return _calculate_asset_reference_index(value, asset_references)
        case ABIReferenceType.APPLICATION:
            return _calculate_application_reference_index(value, app_id, app_references)
    msg = f"Unsupported ABI reference type: {reference_type}"
    raise ValueError(msg)


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


def _encode_args_individually(abi_types: Sequence[ABIType], abi_values: Sequence) -> list[bytes]:
    return [
        abi_type.encode(_prepare_value_for_encoding(abi_type, abi_values[idx]))
        for idx, abi_type in enumerate(abi_types)
    ]


def _encode_args_with_tuple_packing(abi_types: Sequence[ABIType], abi_values: Sequence) -> list[bytes]:
    encoded: list[bytes] = []
    first_types = abi_types[:ARGS_TUPLE_PACKING_THRESHOLD]
    first_values = abi_values[:ARGS_TUPLE_PACKING_THRESHOLD]
    encoded.extend(_encode_args_individually(first_types, first_values))

    remaining_types = abi_types[ARGS_TUPLE_PACKING_THRESHOLD:]
    remaining_values = abi_values[ARGS_TUPLE_PACKING_THRESHOLD:]
    if remaining_types:
        tuple_type = TupleType(list(remaining_types))
        encoded.append(tuple_type.encode(_prepare_value_for_encoding(tuple_type, list(remaining_values))))
    return encoded


def _to_tuple(values: Sequence | None) -> list | None:
    if values is None:
        return None
    return list(values) if values else None


def _prepare_value_for_encoding(abi_type: ABIType, value: object) -> object:
    """Ensure ABI values are shaped correctly for encoding, especially structs."""

    if isinstance(abi_type, algokit_abi.StructType):
        if isinstance(value, Mapping):
            return {
                field_name: _prepare_value_for_encoding(field_type, value[field_name])
                for field_name, field_type in abi_type.fields.items()
            }
        value_seq = list(value)
        return {
            field_name: _prepare_value_for_encoding(field_type, value_seq[idx])
            for idx, (field_name, field_type) in enumerate(abi_type.fields.items())
        }
    if isinstance(abi_type, algokit_abi.TupleType):
        return [
            _prepare_value_for_encoding(element_type, value[idx])
            for idx, element_type in enumerate(abi_type.elements)
        ]
    if isinstance(abi_type, algokit_abi.StaticArrayType | algokit_abi.DynamicArrayType):
        return [_prepare_value_for_encoding(abi_type.element, v) for v in value]
    return value
