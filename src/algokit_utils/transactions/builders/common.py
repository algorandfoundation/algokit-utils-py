import base64
from dataclasses import dataclass, replace
from typing import Protocol, runtime_checkable

from algokit_algod_client import models as algod_models
from algokit_transact import validate_transaction
from algokit_transact.models.app_call import AppCallTransactionFields
from algokit_transact.models.asset_config import AssetConfigTransactionFields
from algokit_transact.models.asset_freeze import AssetFreezeTransactionFields
from algokit_transact.models.asset_transfer import AssetTransferTransactionFields
from algokit_transact.models.key_registration import KeyRegistrationTransactionFields
from algokit_transact.models.payment import PaymentTransactionFields
from algokit_transact.models.transaction import Transaction, TransactionType
from algokit_transact.ops.fees import assign_fee
from algokit_utils.models.amount import AlgoAmount
from algokit_utils.transactions.fee_coverage import FeeDelta
from algokit_utils.transactions.types import CommonTxnParams

LEASE_MIN_LENGTH = 1
LEASE_MAX_LENGTH = 32


@runtime_checkable
class AlgoSuggestedParams(Protocol):
    fee: int
    first: int
    last: int
    gen: str
    gh: str
    flat_fee: bool
    consensus_version: str
    min_fee: int


SuggestedParamsLike = AlgoSuggestedParams | algod_models.SuggestedParams

__all__ = [
    "BuiltTransaction",
    "FeeConfig",
    "SuggestedParamsLike",
    "TransactionHeader",
    "apply_transaction_fees",
    "build_transaction",
    "build_transaction_header",
    "calculate_inner_fee_delta",
    "encode_lease",
]


@dataclass(slots=True)
class TransactionHeader:
    sender: str
    first_valid: int
    last_valid: int
    genesis_hash: bytes
    genesis_id: str | None
    note: bytes | None
    lease: bytes | None
    rekey_to: str | None


@dataclass(slots=True)
class FeeConfig:
    fee_per_byte: int
    min_fee: int
    flat_fee: bool


@dataclass(slots=True)
class BuiltTransaction:
    txn: Transaction
    logical_max_fee: AlgoAmount | None


def build_transaction_header(
    params: CommonTxnParams,
    suggested_params: SuggestedParamsLike,
    *,
    default_validity_window: int,
    default_validity_window_is_explicit: bool,
    is_localnet: bool,
) -> tuple[TransactionHeader, FeeConfig]:
    normalized = _normalize_suggested_params(suggested_params)
    first_valid = params.first_valid_round or normalized.first_valid

    if params.last_valid_round:
        last_valid = params.last_valid_round
    else:
        window = params.validity_window
        if window is None:
            window = 1000 if is_localnet and not default_validity_window_is_explicit else default_validity_window
        last_valid = first_valid + window

    header = TransactionHeader(
        sender=params.sender,
        first_valid=first_valid,
        last_valid=last_valid,
        genesis_hash=normalized.genesis_hash,
        genesis_id=normalized.genesis_id,
        note=params.note,
        lease=encode_lease(params.lease),
        rekey_to=params.rekey_to,
    )
    fee_config = FeeConfig(
        fee_per_byte=normalized.fee,
        min_fee=normalized.min_fee,
        flat_fee=normalized.flat_fee,
    )
    return header, fee_config


def build_transaction(
    txn_type: TransactionType,
    header: TransactionHeader,
    *,
    payment: PaymentTransactionFields | None = None,
    asset_transfer: AssetTransferTransactionFields | None = None,
    asset_config: AssetConfigTransactionFields | None = None,
    asset_freeze: AssetFreezeTransactionFields | None = None,
    application_call: AppCallTransactionFields | None = None,
    key_registration: KeyRegistrationTransactionFields | None = None,
) -> Transaction:
    txn = Transaction(
        transaction_type=txn_type,
        sender=header.sender,
        first_valid=header.first_valid,
        last_valid=header.last_valid,
        genesis_hash=header.genesis_hash,
        genesis_id=header.genesis_id,
        note=header.note,
        rekey_to=header.rekey_to,
        lease=header.lease,
        payment=payment,
        asset_transfer=asset_transfer,
        asset_config=asset_config,
        asset_freeze=asset_freeze,
        application_call=application_call,
        key_registration=key_registration,
    )
    validate_transaction(txn)
    return txn


def apply_transaction_fees(
    txn: Transaction,
    params: CommonTxnParams,
    fee_config: FeeConfig,
) -> BuiltTransaction:
    extra_fee = params.extra_fee.micro_algo if params.extra_fee else None
    max_fee = params.max_fee.micro_algo if params.max_fee else None

    if params.static_fee:
        fee = params.static_fee.micro_algo
        if extra_fee:
            fee += extra_fee
        if max_fee is not None and fee > max_fee:
            raise ValueError(
                f"Transaction fee {fee} µALGO is greater than max fee {max_fee} µALGO",
            )
        txn_with_fee = replace(txn, fee=fee)
    else:
        txn_with_fee = assign_fee(
            txn,
            fee_per_byte=0 if fee_config.flat_fee else fee_config.fee_per_byte,
            min_fee=fee_config.min_fee,
            extra_fee=extra_fee,
            max_fee=max_fee,
        )

    logical_max_fee = _logical_max_fee(params)
    return BuiltTransaction(txn=txn_with_fee, logical_max_fee=logical_max_fee)


def encode_lease(lease: str | bytes | None) -> bytes | None:
    if lease is None:
        return None
    if isinstance(lease, bytes):
        if not (LEASE_MIN_LENGTH <= len(lease) <= LEASE_MAX_LENGTH):
            raise ValueError(
                (
                    "Received invalid lease; expected something with length between "
                    f"{LEASE_MIN_LENGTH} and {LEASE_MAX_LENGTH}, but received bytes with length {len(lease)}"
                ),
            )
        if len(lease) == LEASE_MAX_LENGTH:
            return lease
        data = bytearray(LEASE_MAX_LENGTH)
        data[: len(lease)] = lease
        return bytes(data)
    encoded = lease.encode("utf-8")
    if not (LEASE_MIN_LENGTH <= len(encoded) <= LEASE_MAX_LENGTH):
        raise ValueError(
            (
                "Received invalid lease; expected something with length between "
                f"{LEASE_MIN_LENGTH} and {LEASE_MAX_LENGTH}, but received '{lease}' with length {len(lease)}"
            ),
        )
    data = bytearray(LEASE_MAX_LENGTH)
    data[: len(encoded)] = encoded
    return bytes(data)


@dataclass(slots=True)
class _NormalizedSuggestedParams:
    first_valid: int
    last_valid: int
    genesis_hash: bytes
    genesis_id: str | None
    fee: int
    min_fee: int
    flat_fee: bool


def _normalize_suggested_params(sp: SuggestedParamsLike) -> _NormalizedSuggestedParams:
    if isinstance(sp, AlgoSuggestedParams):
        genesis_hash = base64.b64decode(sp.gh) if isinstance(sp.gh, str) else sp.gh
        return _NormalizedSuggestedParams(
            first_valid=sp.first,
            last_valid=sp.last,
            genesis_hash=genesis_hash,
            genesis_id=sp.gen,
            fee=sp.fee,
            min_fee=sp.min_fee,
            flat_fee=sp.flat_fee,
        )
    # Typed client SuggestedParams
    genesis_hash = sp.genesis_hash if isinstance(sp.genesis_hash, bytes) else bytes(sp.genesis_hash)
    return _NormalizedSuggestedParams(
        first_valid=sp.first_valid,
        last_valid=sp.last_valid,
        genesis_hash=genesis_hash,
        genesis_id=sp.genesis_id,
        fee=sp.fee,
        min_fee=sp.min_fee,
        flat_fee=sp.flat_fee,
    )


def _logical_max_fee(params: CommonTxnParams) -> AlgoAmount | None:
    if params.max_fee and (params.static_fee is None or params.max_fee.micro_algo > params.static_fee.micro_algo):
        return params.max_fee
    return params.static_fee


def calculate_inner_fee_delta(
    inner_txns: list[algod_models.PendingTransactionResponse] | None,
    min_fee: int,
    acc: FeeDelta | None = None,
) -> FeeDelta | None:
    if not inner_txns:
        return acc

    current = acc
    for inner in reversed(inner_txns):
        recursive_delta = calculate_inner_fee_delta(inner.inner_txns, min_fee, current)
        txn_fee = inner.txn.txn.fee or 0
        txn_fee_delta = FeeDelta.from_int(min_fee - txn_fee)
        combined = FeeDelta.add(recursive_delta, txn_fee_delta)

        if combined and FeeDelta.is_surplus(combined):
            current = None
            continue

        current = combined

    return current
