from algokit_transact.models.asset_config import AssetConfigTransactionFields
from algokit_transact.models.asset_freeze import AssetFreezeTransactionFields
from algokit_transact.models.asset_transfer import AssetTransferTransactionFields
from algokit_transact.models.transaction import TransactionType
from algokit_utils.transactions.builders.common import (
    BuiltTransaction,
    SuggestedParamsLike,
    apply_transaction_fees,
    build_transaction,
    build_transaction_header,
)
from algokit_utils.transactions.types import (
    AssetConfigParams,
    AssetCreateParams,
    AssetDestroyParams,
    AssetFreezeParams,
    AssetOptInParams,
    AssetOptOutParams,
    AssetTransferParams,
    CommonTxnParams,
)

AssetFieldPayload = AssetConfigTransactionFields | AssetFreezeTransactionFields | AssetTransferTransactionFields

__all__ = [
    "build_asset_config_transaction",
    "build_asset_create_transaction",
    "build_asset_destroy_transaction",
    "build_asset_freeze_transaction",
    "build_asset_opt_in_transaction",
    "build_asset_opt_out_transaction",
    "build_asset_transfer_transaction",
]


def _build_transaction(
    params: CommonTxnParams,
    suggested_params: SuggestedParamsLike,
    *,
    txn_type: TransactionType,
    field_payload: AssetFieldPayload,
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
    txn = build_transaction(
        txn_type,
        header,
        asset_config=field_payload if isinstance(field_payload, AssetConfigTransactionFields) else None,
        asset_transfer=field_payload if isinstance(field_payload, AssetTransferTransactionFields) else None,
        asset_freeze=field_payload if isinstance(field_payload, AssetFreezeTransactionFields) else None,
    )
    return apply_transaction_fees(txn, params, fee_config)


def build_asset_create_transaction(
    params: AssetCreateParams,
    suggested_params: SuggestedParamsLike,
    *,
    default_validity_window: int,
    default_validity_window_is_explicit: bool,
    is_localnet: bool,
) -> BuiltTransaction:
    fields = AssetConfigTransactionFields(
        asset_id=0,
        total=params.total,
        decimals=params.decimals,
        default_frozen=params.default_frozen,
        unit_name=params.unit_name,
        asset_name=params.asset_name,
        url=params.url,
        metadata_hash=params.metadata_hash,
        manager=params.manager,
        reserve=params.reserve,
        freeze=params.freeze,
        clawback=params.clawback,
    )
    return _build_transaction(
        params,
        suggested_params,
        txn_type=TransactionType.AssetConfig,
        field_payload=fields,
        default_validity_window=default_validity_window,
        default_validity_window_is_explicit=default_validity_window_is_explicit,
        is_localnet=is_localnet,
    )


def build_asset_config_transaction(
    params: AssetConfigParams,
    suggested_params: SuggestedParamsLike,
    *,
    default_validity_window: int,
    default_validity_window_is_explicit: bool,
    is_localnet: bool,
) -> BuiltTransaction:
    fields = AssetConfigTransactionFields(
        asset_id=params.asset_id,
        manager=params.manager,
        reserve=params.reserve,
        freeze=params.freeze,
        clawback=params.clawback,
    )
    return _build_transaction(
        params,
        suggested_params,
        txn_type=TransactionType.AssetConfig,
        field_payload=fields,
        default_validity_window=default_validity_window,
        default_validity_window_is_explicit=default_validity_window_is_explicit,
        is_localnet=is_localnet,
    )


def build_asset_destroy_transaction(
    params: AssetDestroyParams,
    suggested_params: SuggestedParamsLike,
    *,
    default_validity_window: int,
    default_validity_window_is_explicit: bool,
    is_localnet: bool,
) -> BuiltTransaction:
    fields = AssetConfigTransactionFields(asset_id=params.asset_id)
    return _build_transaction(
        params,
        suggested_params,
        txn_type=TransactionType.AssetConfig,
        field_payload=fields,
        default_validity_window=default_validity_window,
        default_validity_window_is_explicit=default_validity_window_is_explicit,
        is_localnet=is_localnet,
    )


def build_asset_freeze_transaction(
    params: AssetFreezeParams,
    suggested_params: SuggestedParamsLike,
    *,
    default_validity_window: int,
    default_validity_window_is_explicit: bool,
    is_localnet: bool,
) -> BuiltTransaction:
    fields = AssetFreezeTransactionFields(
        asset_id=params.asset_id,
        freeze_target=params.account,
        frozen=params.frozen,
    )
    return _build_transaction(
        params,
        suggested_params,
        txn_type=TransactionType.AssetFreeze,
        field_payload=fields,
        default_validity_window=default_validity_window,
        default_validity_window_is_explicit=default_validity_window_is_explicit,
        is_localnet=is_localnet,
    )


def build_asset_transfer_transaction(
    params: AssetTransferParams,
    suggested_params: SuggestedParamsLike,
    *,
    default_validity_window: int,
    default_validity_window_is_explicit: bool,
    is_localnet: bool,
) -> BuiltTransaction:
    fields = AssetTransferTransactionFields(
        asset_id=params.asset_id,
        amount=params.amount,
        receiver=params.receiver,
        close_remainder_to=params.close_asset_to,
        asset_sender=params.clawback_target,
    )
    return _build_transaction(
        params,
        suggested_params,
        txn_type=TransactionType.AssetTransfer,
        field_payload=fields,
        default_validity_window=default_validity_window,
        default_validity_window_is_explicit=default_validity_window_is_explicit,
        is_localnet=is_localnet,
    )


def build_asset_opt_in_transaction(
    params: AssetOptInParams,
    suggested_params: SuggestedParamsLike,
    *,
    default_validity_window: int,
    default_validity_window_is_explicit: bool,
    is_localnet: bool,
) -> BuiltTransaction:
    transfer_params = AssetTransferParams(
        sender=params.sender,
        signer=params.signer,
        rekey_to=params.rekey_to,
        note=params.note,
        lease=params.lease,
        static_fee=params.static_fee,
        extra_fee=params.extra_fee,
        max_fee=params.max_fee,
        validity_window=params.validity_window,
        first_valid_round=params.first_valid_round,
        last_valid_round=params.last_valid_round,
        asset_id=params.asset_id,
        amount=0,
        receiver=params.sender,
    )
    return build_asset_transfer_transaction(
        transfer_params,
        suggested_params,
        default_validity_window=default_validity_window,
        default_validity_window_is_explicit=default_validity_window_is_explicit,
        is_localnet=is_localnet,
    )


def build_asset_opt_out_transaction(
    params: AssetOptOutParams,
    suggested_params: SuggestedParamsLike,
    *,
    default_validity_window: int,
    default_validity_window_is_explicit: bool,
    is_localnet: bool,
) -> BuiltTransaction:
    transfer_params = AssetTransferParams(
        sender=params.sender,
        signer=params.signer,
        rekey_to=params.rekey_to,
        note=params.note,
        lease=params.lease,
        static_fee=params.static_fee,
        extra_fee=params.extra_fee,
        max_fee=params.max_fee,
        validity_window=params.validity_window,
        first_valid_round=params.first_valid_round,
        last_valid_round=params.last_valid_round,
        asset_id=params.asset_id,
        amount=0,
        receiver=params.sender,
        close_asset_to=params.creator,
    )
    return build_asset_transfer_transaction(
        transfer_params,
        suggested_params,
        default_validity_window=default_validity_window,
        default_validity_window_is_explicit=default_validity_window_is_explicit,
        is_localnet=is_localnet,
    )
