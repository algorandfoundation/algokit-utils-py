import base64

from algokit_transact.models.key_registration import KeyRegistrationTransactionFields
from algokit_transact.models.transaction import TransactionType
from algokit_utils.transactions.builders.common import (
    BuiltTransaction,
    SuggestedParamsLike,
    apply_transaction_fees,
    build_transaction,
    build_transaction_header,
)
from algokit_utils.transactions.types import OfflineKeyRegistrationParams, OnlineKeyRegistrationParams

__all__ = ["build_offline_key_registration_transaction", "build_online_key_registration_transaction"]

STATE_PROOF_KEY_LENGTH = 64


def build_online_key_registration_transaction(
    params: OnlineKeyRegistrationParams,
    suggested_params: SuggestedParamsLike,
    *,
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
    fields = KeyRegistrationTransactionFields(
        vote_key=_decode_key(params.vote_key),
        selection_key=_decode_key(params.selection_key),
        vote_first=params.vote_first,
        vote_last=params.vote_last,
        vote_key_dilution=params.vote_key_dilution,
        state_proof_key=_decode_state_proof_key(params.state_proof_key),
        non_participation=params.nonparticipation,
    )
    txn = build_transaction(
        TransactionType.KeyRegistration,
        header,
        key_registration=fields,
    )
    return apply_transaction_fees(txn, params, fee_config)


def build_offline_key_registration_transaction(
    params: OfflineKeyRegistrationParams,
    suggested_params: SuggestedParamsLike,
    *,
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
    fields = KeyRegistrationTransactionFields(
        non_participation=params.prevent_account_from_ever_participating_again,
    )
    txn = build_transaction(TransactionType.KeyRegistration, header, key_registration=fields)
    return apply_transaction_fees(txn, params, fee_config)


def _decode_key(value: str | bytes | None) -> bytes | None:
    if value is None:
        return None
    if isinstance(value, bytes):
        return value
    try:
        return base64.b64decode(value)
    except Exception as exc:
        raise ValueError("Vote/selection keys must be base64-encoded strings") from exc


def _decode_state_proof_key(value: str | bytes | None) -> bytes | None:
    if value is None:
        return None
    if isinstance(value, bytes):
        if len(value) == STATE_PROOF_KEY_LENGTH:
            return value
        try:
            decoded = base64.b64decode(value)
        except Exception as exc:
            raise ValueError("State proof keys must be 64 bytes or base64-encoded strings") from exc
        if len(decoded) != STATE_PROOF_KEY_LENGTH:
            raise ValueError("State proof keys must be 64 bytes or base64-encoded strings")
        return decoded
    try:
        decoded = base64.b64decode(value)
    except Exception as exc:
        raise ValueError("State proof keys must be base64-encoded strings") from exc
    if len(decoded) != STATE_PROOF_KEY_LENGTH:
        raise ValueError("State proof keys must decode to 64 bytes")
    return decoded
