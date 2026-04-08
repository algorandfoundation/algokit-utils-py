from collections.abc import Sequence

from algokit_transact.models.app_call import AppCallTransactionFields
from algokit_transact.models.app_call import BoxReference as TxBoxReference
from algokit_transact.models.common import OnApplicationComplete, StateSchema
from algokit_transact.models.transaction import TransactionType
from algokit_utils.applications.app_manager import AppManager
from algokit_utils.models.state import BoxIdentifier, BoxReference
from algokit_utils.transactions.builders.common import (
    BuiltTransaction,
    SuggestedParamsLike,
    apply_transaction_fees,
    build_transaction,
    build_transaction_header,
)
from algokit_utils.transactions.helpers import calculate_extra_program_pages
from algokit_utils.transactions.types import (
    AppCallParams,
    AppCreateParams,
    AppCreateSchema,
    AppDeleteParams,
    AppMethodCallParams,
    AppUpdateParams,
)

AppParams = AppCallParams | AppCreateParams | AppDeleteParams | AppMethodCallParams | AppUpdateParams

__all__ = [
    "build_app_call_transaction",
    "build_app_create_transaction",
    "build_app_delete_transaction",
    "build_app_method_call_transaction",
    "build_app_update_transaction",
]


def build_app_create_transaction(
    params: AppCreateParams,
    suggested_params: SuggestedParamsLike,
    *,
    app_manager: AppManager,
    default_validity_window: int,
    default_validity_window_is_explicit: bool,
    is_localnet: bool,
) -> BuiltTransaction:
    approval = _compile_program(app_manager, params.approval_program)
    clear = _compile_program(app_manager, params.clear_state_program)

    schema = params.schema or AppCreateSchema(
        global_ints=0,
        global_byte_slices=0,
        local_ints=0,
        local_byte_slices=0,
    )
    global_schema = StateSchema(num_uints=schema["global_ints"], num_byte_slices=schema["global_byte_slices"])
    local_schema = StateSchema(num_uints=schema["local_ints"], num_byte_slices=schema["local_byte_slices"])

    fields = _build_app_call_fields(
        params,
        app_id=0,
        approval_program=approval,
        clear_state_program=clear,
        global_state_schema=global_schema,
        local_state_schema=local_schema,
        extra_program_pages=params.extra_program_pages or calculate_extra_program_pages(approval, clear),
        app_manager=app_manager,
    )
    return _build_app_transaction(
        params=params,
        suggested_params=suggested_params,
        fields=fields,
        default_validity_window=default_validity_window,
        default_validity_window_is_explicit=default_validity_window_is_explicit,
        is_localnet=is_localnet,
    )


def build_app_update_transaction(
    params: AppUpdateParams,
    suggested_params: SuggestedParamsLike,
    *,
    app_manager: AppManager,
    default_validity_window: int,
    default_validity_window_is_explicit: bool,
    is_localnet: bool,
) -> BuiltTransaction:
    approval = _compile_program(app_manager, params.approval_program)
    clear = _compile_program(app_manager, params.clear_state_program)
    fields = _build_app_call_fields(
        params,
        app_id=params.app_id,
        approval_program=approval,
        clear_state_program=clear,
        app_manager=app_manager,
    )
    return _build_app_transaction(
        params=params,
        suggested_params=suggested_params,
        fields=fields,
        default_validity_window=default_validity_window,
        default_validity_window_is_explicit=default_validity_window_is_explicit,
        is_localnet=is_localnet,
    )


def build_app_delete_transaction(
    params: AppDeleteParams,
    suggested_params: SuggestedParamsLike,
    *,
    app_manager: AppManager,
    default_validity_window: int,
    default_validity_window_is_explicit: bool,
    is_localnet: bool,
) -> BuiltTransaction:
    fields = _build_app_call_fields(
        params,
        app_id=params.app_id,
        app_manager=app_manager,
    )
    return _build_app_transaction(
        params=params,
        suggested_params=suggested_params,
        fields=fields,
        default_validity_window=default_validity_window,
        default_validity_window_is_explicit=default_validity_window_is_explicit,
        is_localnet=is_localnet,
    )


def build_app_call_transaction(
    params: AppCallParams,
    suggested_params: SuggestedParamsLike,
    *,
    app_manager: AppManager,
    default_validity_window: int,
    default_validity_window_is_explicit: bool,
    is_localnet: bool,
) -> BuiltTransaction:
    fields = _build_app_call_fields(
        params,
        app_id=params.app_id,
        app_manager=app_manager,
    )
    return _build_app_transaction(
        params=params,
        suggested_params=suggested_params,
        fields=fields,
        default_validity_window=default_validity_window,
        default_validity_window_is_explicit=default_validity_window_is_explicit,
        is_localnet=is_localnet,
    )


def build_app_method_call_transaction(
    params: AppMethodCallParams,
    suggested_params: SuggestedParamsLike,
    *,
    app_manager: AppManager,
    default_validity_window: int,
    default_validity_window_is_explicit: bool,
    is_localnet: bool,
) -> BuiltTransaction:
    fields = _build_app_call_fields(
        params,
        app_id=params.app_id,
        app_manager=app_manager,
    )
    return _build_app_transaction(
        params=params,
        suggested_params=suggested_params,
        fields=fields,
        default_validity_window=default_validity_window,
        default_validity_window_is_explicit=default_validity_window_is_explicit,
        is_localnet=is_localnet,
    )


def _build_app_transaction(
    params: AppParams,
    suggested_params: SuggestedParamsLike,
    *,
    fields: AppCallTransactionFields,
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
    txn = build_transaction(TransactionType.AppCall, header, application_call=fields)
    return apply_transaction_fees(txn, params, fee_config)


def _build_app_call_fields(
    params: AppParams,
    *,
    app_id: int,
    app_manager: AppManager,
    approval_program: bytes | None = None,
    clear_state_program: bytes | None = None,
    global_state_schema: StateSchema | None = None,
    local_state_schema: StateSchema | None = None,
    extra_program_pages: int | None = None,
) -> AppCallTransactionFields:
    return AppCallTransactionFields(
        app_id=app_id,
        on_complete=params.on_complete or OnApplicationComplete.NoOp,
        approval_program=approval_program,
        clear_state_program=clear_state_program,
        global_state_schema=global_state_schema,
        local_state_schema=local_state_schema,
        args=_to_tuple(params.args),
        account_references=_to_tuple(params.account_references),
        app_references=_to_tuple(params.app_references),
        asset_references=_to_tuple(params.asset_references),
        extra_program_pages=extra_program_pages,
        box_references=_convert_box_references(params.box_references, app_manager),
    )


def _compile_program(app_manager: AppManager, program: bytes | str) -> bytes:
    if isinstance(program, bytes):
        return program
    compiled = app_manager.compile_teal(program)
    return compiled.compiled_base64_to_bytes


def _to_tuple(items: Sequence | None) -> list | None:
    if not items:
        return None
    return list(items)


def _convert_box_references(
    box_refs: list[BoxReference | BoxIdentifier] | None,
    app_manager: AppManager,
) -> list[TxBoxReference] | None:
    if not box_refs:
        return None
    converted: list[TxBoxReference] = []
    for ref in box_refs:
        app_id, name = app_manager.get_box_reference(ref)
        converted.append(TxBoxReference(app_id=app_id, name=name))
    return converted if converted else None
