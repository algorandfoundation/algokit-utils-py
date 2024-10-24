from __future__ import annotations

import math
from dataclasses import dataclass
from typing import (
    TYPE_CHECKING,
    Any,
    TypeVar,
)

import algosdk
import algosdk.atomic_transaction_composer
from algosdk import encoding
from algosdk.atomic_transaction_composer import (
    AtomicTransactionComposer,
    EmptySigner,
    TransactionSigner,
    TransactionWithSigner,
)
from algosdk.constants import MIN_TXN_FEE
from algosdk.transaction import (
    OnComplete,
    SuggestedParams,
    Transaction,
)
from deprecated import deprecated

from algokit_utils._debugging import simulate_and_persist_response, simulate_response
from algokit_utils.applications.app_manager import AppManager
from algokit_utils.config import config

if TYPE_CHECKING:
    from collections.abc import Callable

    from algosdk.abi import Method
    from algosdk.box_reference import BoxReference
    from algosdk.v2client.algod import AlgodClient

    from algokit_utils.models.amount import AlgoAmount


@dataclass(frozen=True)
class SenderParam:
    sender: str


@dataclass(frozen=True)
class CommonTransactionParams:
    sender: str
    signer: TransactionSigner | None = None
    rekey_to: str | None = None
    note: bytes | None = None
    lease: bytes | None = None
    static_fee: AlgoAmount | None = None
    extra_fee: AlgoAmount | None = None
    max_fee: AlgoAmount | None = None
    validity_window: int | None = None
    first_valid_round: int | None = None
    last_valid_round: int | None = None


@dataclass(frozen=True)
class _RequiredPaymentTxnParams(SenderParam):
    receiver: str
    amount: AlgoAmount


@dataclass(frozen=True)
class PaymentParams(CommonTransactionParams, _RequiredPaymentTxnParams):
    close_remainder_to: str | None = None


@dataclass(frozen=True)
class _RequiredAssetCreateParams(SenderParam):
    total: int


@dataclass(frozen=True)
class AssetCreateParams(CommonTransactionParams, _RequiredAssetCreateParams):
    decimals: int | None = None
    default_frozen: bool | None = None
    manager: str | None = None
    reserve: str | None = None
    freeze: str | None = None
    clawback: str | None = None
    unit_name: str | None = None
    asset_name: str | None = None
    url: str | None = None
    metadata_hash: bytes | None = None


@dataclass(frozen=True)
class _RequiredAssetConfigParams(SenderParam):
    asset_id: int


@dataclass(frozen=True)
class AssetConfigParams(CommonTransactionParams, _RequiredAssetConfigParams):
    manager: str | None = None
    reserve: str | None = None
    freeze: str | None = None
    clawback: str | None = None


@dataclass(frozen=True)
class _RequiredAssetFreezeParams(SenderParam):
    asset_id: int
    account: str
    frozen: bool


@dataclass(frozen=True)
class AssetFreezeParams(CommonTransactionParams, _RequiredAssetFreezeParams):
    pass


@dataclass(frozen=True)
class _RequiredAssetDestroyParams(SenderParam):
    asset_id: int


@dataclass(frozen=True)
class AssetDestroyParams(CommonTransactionParams, _RequiredAssetDestroyParams):
    pass


@dataclass(frozen=True)
class _RequiredAssetTransferParams(SenderParam):
    asset_id: int
    amount: int
    receiver: str


@dataclass(frozen=True)
class AssetTransferParams(CommonTransactionParams, _RequiredAssetTransferParams):
    clawback_target: str | None = None
    close_asset_to: str | None = None


@dataclass(frozen=True)
class _RequiredAssetOptInParams(SenderParam):
    asset_id: int


@dataclass(frozen=True)
class AssetOptInParams(CommonTransactionParams, _RequiredAssetOptInParams):
    pass


@dataclass(frozen=True)
class _RequiredAssetOptOutParams(SenderParam):
    asset_id: int
    creator: str


@dataclass(frozen=True)
class AssetOptOutParams(CommonTransactionParams, _RequiredAssetOptOutParams):
    pass


@dataclass(frozen=True)
class _RequiredOnlineKeyRegParams(SenderParam):
    vote_key: str
    selection_key: str
    vote_first: int
    vote_last: int
    vote_key_dilution: int


@dataclass(frozen=True)
class OnlineKeyRegParams(CommonTransactionParams, _RequiredOnlineKeyRegParams):
    state_proof_key: bytes | None = None


@dataclass(frozen=True)
class CommonAppCallParams(CommonTransactionParams, SenderParam):
    app_id: int | None = None
    on_complete: OnComplete | None = None
    args: list[bytes] | None = None
    account_references: list[str] | None = None
    app_references: list[int] | None = None
    asset_references: list[int] | None = None
    box_references: list[BoxReference] | None = None


@dataclass(frozen=True)
class _RequiredAppCreateParams:
    approval_program: bytearray | str
    clear_program: bytearray | str


@dataclass(frozen=True)
class _AppCreateSchema:
    global_ints: int
    global_bytes: int
    local_ints: int
    local_bytes: int


@dataclass(frozen=True)
class AppCreateParams(CommonAppCallParams, _RequiredAppCreateParams):
    on_complete: OnComplete | None = None
    schema: _AppCreateSchema | None = None
    extra_program_pages: int | None = None


@dataclass(frozen=True)
class _RequiredAppUpdateParams:
    approval_program: bytearray | str
    clear_program: bytearray | str


@dataclass(frozen=True)
class AppUpdateParams(CommonAppCallParams, _RequiredAppUpdateParams):
    on_complete: OnComplete | None = None


@dataclass(frozen=True)
class AppCallParams(CommonAppCallParams):
    on_complete: OnComplete | None = None


@dataclass(frozen=True)
class AppDeleteParams(CommonAppCallParams):
    on_complete: OnComplete | None = None


@dataclass(frozen=True)
class AppMethodCallParams(CommonAppCallParams):
    on_complete: OnComplete | None = None


T = TypeVar("T", bound=CommonAppCallParams)


class AppCreateMethodCall(AppMethodCallParams):
    pass


class AppDeleteMethodCall(AppMethodCallParams):
    pass


class AppUpdateMethodCall(AppMethodCallParams):
    pass


class AppCallMethodCall(AppMethodCallParams):
    pass


TxnParams = (
    PaymentParams
    | AssetCreateParams
    | AssetConfigParams
    | AssetFreezeParams
    | AssetDestroyParams
    | OnlineKeyRegParams
    | AssetTransferParams
    | AssetOptInParams
    | AssetOptOutParams
    | AppCallParams
    | TransactionWithSigner
    | AppCreateMethodCall
    | AppUpdateMethodCall
    | AppDeleteMethodCall
    | AppCallMethodCall
)


@dataclass
class BuiltTransactions:
    """
    Set of transactions built by TransactionComposer.

    :param transactions: The built transactions.
    :param method_calls: Any ABIMethod objects associated with any of the transactions in a map keyed by transaction index.
    :param signers: Any TransactionSigner objects associated with any of the transactions in a map keyed by transaction index.
    """

    transactions: list[Transaction]
    method_calls: dict[int, Method]
    signers: dict[int, TransactionSigner]


class TransactionComposer:
    NULL_SIGNER: TransactionSigner = EmptySigner()

    def __init__(  # noqa: PLR0913
        self,
        algod: AlgodClient,
        get_signer: Callable[[str], TransactionSigner],
        get_suggested_params: Callable[[], SuggestedParams] | None = None,
        default_validity_window: int | None = None,
        app_manager: AppManager | None = None,
    ):
        self.algod: AlgodClient = algod
        self.get_suggested_params = get_suggested_params or algod.suggested_params
        self.get_signer: Callable[[str], TransactionSigner] = get_signer
        self.default_validity_window: int = default_validity_window or 10
        self.default_validity_window_is_explicit = default_validity_window is not None
        self.txns: list[TransactionWithSigner | TxnParams | AtomicTransactionComposer] = []
        self.atc: AtomicTransactionComposer = AtomicTransactionComposer()
        self.txn_method_map: dict[str, Method] = {}
        self.app_manager = app_manager or AppManager(algod)

    def add_transaction(self, transaction: Transaction, signer: TransactionSigner | None = None) -> TransactionComposer:
        signer = signer or self.get_signer(algosdk.encoding.encode_address(transaction.sender))
        self.txns.append(TransactionWithSigner(transaction, signer))
        return self

    def add_payment(self, params: PaymentParams) -> TransactionComposer:
        self.txns.append(params)
        return self

    def add_asset_create(self, params: AssetCreateParams) -> TransactionComposer:
        self.txns.append(params)
        return self

    def add_asset_config(self, params: AssetConfigParams) -> TransactionComposer:
        self.txns.append(params)
        return self

    def add_asset_freeze(self, params: AssetFreezeParams) -> TransactionComposer:
        self.txns.append(params)
        return self

    def add_asset_destroy(self, params: AssetDestroyParams) -> TransactionComposer:
        self.txns.append(params)
        return self

    def add_asset_transfer(self, params: AssetTransferParams) -> TransactionComposer:
        self.txns.append(params)
        return self

    def add_asset_opt_in(self, params: AssetOptInParams) -> TransactionComposer:
        self.txns.append(params)
        return self

    def add_asset_opt_out(self, params: AssetOptOutParams) -> TransactionComposer:
        self.txns.append(params)
        return self

    def add_app_call(self, params: AppCallParams) -> TransactionComposer:
        self.txns.append(params)
        return self

    def add_online_key_reg(self, params: OnlineKeyRegParams) -> TransactionComposer:
        self.txns.append(params)
        return self

    def add_app_create_method_call(self, params: AppCreateMethodCall) -> TransactionComposer:
        self.txns.append(params)
        return self

    def add_app_update_method_call(self, params: AppUpdateMethodCall) -> TransactionComposer:
        self.txns.append(params)
        return self

    def add_app_delete_method_call(self, params: AppDeleteMethodCall) -> TransactionComposer:
        self.txns.append(params)
        return self

    def add_app_call_method_call(self, params: AppCallMethodCall) -> TransactionComposer:
        self.txns.append(params)
        return self

    def add_atc(self, atc: AtomicTransactionComposer) -> TransactionComposer:
        self.txns.append(atc)
        return self

    def _build_atc(
        self,
        atc: AtomicTransactionComposer,
        process_transaction: Callable[[Transaction, int], Transaction] | None = None,
    ) -> list[TransactionWithSigner]:
        group = atc.build_group()

        txn_with_signers: list[TransactionWithSigner] = []
        for idx, ts in enumerate(group):
            ts.txn.group = None
            if process_transaction:
                ts.txn = process_transaction(ts.txn, idx)
            method = atc.method_dict.get(len(group) - 1)
            if method:
                self.txn_method_map[ts.txn.get_txid()] = method
            txn_with_signers.append(ts)

        return txn_with_signers

    def _common_txn_build_step(
        self,
        params: CommonTransactionParams | AppMethodCallParams,
        txn: Transaction,
        suggested_params: SuggestedParams,
    ) -> Transaction:
        if params.lease:
            txn.lease = params.lease
        if params.rekey_to:
            txn.rekey_to = encoding.decode_address(params.rekey_to)
        if params.note:
            txn.note = params.note

        if params.first_valid_round:
            txn.first_valid_round = params.first_valid_round

        if params.last_valid_round:
            txn.last_valid_round = params.last_valid_round
        else:
            txn.last_valid_round = txn.first_valid_round + (params.validity_window or self.default_validity_window)

        if params.static_fee is not None and params.extra_fee is not None:
            raise ValueError("Cannot set both static_fee and extra_fee")

        if params.static_fee is not None:
            txn.fee = params.static_fee
        else:
            txn.fee = txn.estimate_size() * (suggested_params.fee or MIN_TXN_FEE)
            if params.extra_fee:
                txn.fee += params.extra_fee.micro_algos

        if params.max_fee is not None and txn.fee > params.max_fee:
            raise ValueError(f"Transaction fee {txn.fee} is greater than max_fee {params.max_fee}")

        return txn

    def _build_payment(self, params: PaymentParams, suggested_params: SuggestedParams) -> Transaction:
        txn = algosdk.transaction.PaymentTxn(
            sender=params.sender,
            sp=suggested_params,
            receiver=params.receiver,
            amt=params.amount,
            close_remainder_to=params.close_remainder_to,
        )

        return self._common_txn_build_step(params, txn, suggested_params)

    def _build_asset_create(self, params: AssetCreateParams, suggested_params: SuggestedParams) -> Transaction:
        txn = algosdk.transaction.AssetConfigTxn(
            sender=params.sender,
            sp=suggested_params,
            total=params.total,
            default_frozen=params.default_frozen or False,
            unit_name=params.unit_name,
            asset_name=params.asset_name,
            manager=params.manager,
            reserve=params.reserve,
            freeze=params.freeze,
            clawback=params.clawback,
            url=params.url,
            metadata_hash=params.metadata_hash,
            decimals=params.decimals or 0,
            strict_empty_address_check=False,
        )

        return self._common_txn_build_step(params, txn, suggested_params)

    def _build_asset_config(self, params: AssetConfigParams, suggested_params: SuggestedParams) -> Transaction:
        txn = algosdk.transaction.AssetConfigTxn(
            sender=params.sender,
            sp=suggested_params,
            index=params.asset_id,
            manager=params.manager,
            reserve=params.reserve,
            freeze=params.freeze,
            clawback=params.clawback,
            strict_empty_address_check=False,
        )

        return self._common_txn_build_step(params, txn, suggested_params)

    def _build_asset_destroy(self, params: AssetDestroyParams, suggested_params: SuggestedParams) -> Transaction:
        txn = algosdk.transaction.AssetDestroyTxn(
            sender=params.sender,
            sp=suggested_params,
            index=params.asset_id,
        )

        return self._common_txn_build_step(params, txn, suggested_params)

    def _build_asset_freeze(self, params: AssetFreezeParams, suggested_params: SuggestedParams) -> Transaction:
        txn = algosdk.transaction.AssetFreezeTxn(
            sender=params.sender,
            sp=suggested_params,
            index=params.asset_id,
            target=params.account,
            new_freeze_state=params.frozen,
        )

        return self._common_txn_build_step(params, txn, suggested_params)

    def _build_asset_transfer(self, params: AssetTransferParams, suggested_params: SuggestedParams) -> Transaction:
        txn = algosdk.transaction.AssetTransferTxn(
            sender=params.sender,
            sp=suggested_params,
            receiver=params.receiver,
            amt=params.amount,
            index=params.asset_id,
            close_assets_to=params.close_asset_to,
            revocation_target=params.clawback_target,
        )

        return self._common_txn_build_step(params, txn, suggested_params)

    def _build_app_call(
        self, params: AppCallParams | AppUpdateParams | AppCreateParams, suggested_params: SuggestedParams
    ) -> Transaction:
        app_id = params.app_id or None

        approval_program = None
        clear_program = None

        if isinstance(params, AppUpdateParams | AppCreateParams):
            if isinstance(params.approval_program, str):
                approval_program = self.app_manager.compile_teal(params.approval_program).compiled_base64_to_bytes
            elif isinstance(params.approval_program, bytes):
                approval_program = params.approval_program

            if isinstance(params.clear_program, str):
                clear_program = self.app_manager.compile_teal(params.clear_program).compiled_base64_to_bytes
            elif isinstance(params.clear_program, bytes):
                clear_program = params.clear_program

        approval_program_len = len(approval_program) if approval_program else 0
        clear_program_len = len(clear_program) if clear_program else 0

        sdk_params = {
            "sender": params.sender,
            "sp": suggested_params,
            "app_args": params.args,
            "on_complete": params.on_complete or OnComplete.NoOpOC,
            "accounts": params.account_references,
            "foreign_apps": params.app_references,
            "foreign_assets": params.asset_references,
            "boxes": params.box_references,
            "approval_program": approval_program,
            "clear_program": clear_program,
        }

        if not app_id and isinstance(params, AppCreateParams):
            if not sdk_params["approval_program"] or not sdk_params["clear_program"]:
                raise ValueError("approval_program and clear_program are required for application creation")

            txn = algosdk.transaction.ApplicationCreateTxn(
                **sdk_params,
                extra_pages=params.extra_program_pages
                or math.floor((approval_program_len + clear_program_len) / algosdk.constants.APP_PAGE_MAX_SIZE)
                if params.extra_program_pages
                else 0,
            )
        else:
            txn = algosdk.transaction.ApplicationCallTxn(**sdk_params, index=app_id)  # type: ignore[assignment,no-untyped-call]

        return self._common_txn_build_step(params, txn, suggested_params)

    def _build_key_reg(self, params: OnlineKeyRegParams, suggested_params: SuggestedParams) -> Transaction:
        txn = algosdk.transaction.KeyregTxn(
            sender=params.sender,
            sp=suggested_params,
            votekey=params.vote_key,
            selkey=params.selection_key,
            votefst=params.vote_first,
            votelst=params.vote_last,
            votekd=params.vote_key_dilution,
            rekey_to=params.rekey_to,
            nonpart=False,
            sprfkey=params.state_proof_key,
        )

        return self._common_txn_build_step(params, txn, suggested_params)

    def _is_abi_value(self, x: object) -> bool:
        if isinstance(x, bool | int | float | str | bytes):
            return True
        if isinstance(x, list):
            return all(self._is_abi_value(item) for item in x)
        return False

    def _build_method_call(  # noqa: C901, PLR0912
        self,
        *,
        params: AppCallMethodCall | AppCreateMethodCall | AppUpdateMethodCall,
        suggested_params: SuggestedParams,
        include_signer: bool,
    ) -> list[TransactionWithSigner]:
        method_args: list[Any] = []
        arg_offset = 0

        if params.args:
            for i, arg in enumerate(params.args):
                if self._is_abi_value(arg):
                    method_args.append(arg)
                    continue

                if algosdk.abi.is_abi_transaction_type(params.method.args[i + arg_offset].type):
                    if isinstance(arg, AppCallMethodCall | AppCreateMethodCall | AppUpdateMethodCall):
                        temp_txn_with_signers = self._build_method_call(
                            params=arg,
                            suggested_params=suggested_params,
                            include_signer=include_signer,
                        )
                        method_args.extend(temp_txn_with_signers)
                        arg_offset += len(temp_txn_with_signers) - 1
                        continue
                    if isinstance(arg, AppCallParams):
                        txn = self._build_app_call(arg, suggested_params)
                    elif isinstance(arg, PaymentParams):
                        txn = self._build_payment(arg, suggested_params)
                    elif isinstance(arg, AssetOptInParams):
                        txn = self._build_asset_transfer(
                            AssetTransferParams(**arg.__dict__, receiver=arg.sender, amount=0, signer=arg.signer),
                            suggested_params,
                        )
                    elif isinstance(arg, AssetCreateParams):
                        txn = self._build_asset_create(arg, suggested_params)
                    elif isinstance(arg, AssetConfigParams):
                        txn = self._build_asset_config(arg, suggested_params)
                    elif isinstance(arg, AssetDestroyParams):
                        txn = self._build_asset_destroy(arg, suggested_params)
                    elif isinstance(arg, AssetFreezeParams):
                        txn = self._build_asset_freeze(arg, suggested_params)
                    elif isinstance(arg, AssetTransferParams):
                        txn = self._build_asset_transfer(arg, suggested_params)
                    elif isinstance(arg, OnlineKeyRegParams):
                        txn = self._build_key_reg(arg, suggested_params)
                    else:
                        raise ValueError(f"Unsupported method arg transaction type: {arg}")

                    method_args.append(
                        TransactionWithSigner(
                            txn=txn,
                            signer=(
                                arg.signer.signer
                                if isinstance(arg.signer, TransactionSignerAccount)
                                else arg.signer
                                if arg.signer
                                else self.get_signer(arg.sender)
                                if include_signer
                                else self.NULL_SIGNER
                            ),
                        )
                    )

                    continue

                raise ValueError(f"Unsupported method arg: {arg}")

        method_atc = AtomicTransactionComposer()

        method_atc.add_method_call(
            app_id=params.app_id or 0,
            method=params.method,
            sender=params.sender,
            sp=suggested_params,
            signer=(
                params.signer.signer
                if isinstance(params.signer, TransactionSignerAccount)
                else params.signer
                if params.signer
                else self.get_signer(params.sender)
                if include_signer
                else self.NULL_SIGNER
            ),
            method_args=method_args,
            on_complete=OnComplete.NoOpOC,
            note=params.note,
            lease=params.lease,
        )

        return self._build_atc(
            method_atc,
            process_transaction=lambda txn, idx: self._common_txn_build_step(params, txn, suggested_params)
            if idx == method_atc.get_tx_count() - 1
            else txn,
        )

    def _build_txn(  # noqa: C901, PLR0912, PLR0911
        self,
        txn: TransactionWithSigner | TxnParams | AtomicTransactionComposer,
        suggested_params: SuggestedParams,
    ) -> list[TransactionWithSigner]:
        if isinstance(txn, TransactionWithSigner):
            return [txn]

        if isinstance(txn, AtomicTransactionComposer):
            return self._build_atc(txn)

        if isinstance(txn, AppCallMethodCall | AppCreateMethodCall | AppUpdateMethodCall):
            return self._build_method_call(params=txn, suggested_params=suggested_params, include_signer=True)

        signer = (
            txn.signer
            if isinstance(txn.signer, TransactionSignerAccount)
            else txn.signer
            if txn.signer
            else self.get_signer(txn.sender)
        )

        if isinstance(txn, PaymentParams):
            payment = self._build_payment(txn, suggested_params)
            return [TransactionWithSigner(txn=payment, signer=signer)]
        elif isinstance(txn, AssetCreateParams):
            asset_create = self._build_asset_create(txn, suggested_params)
            return [TransactionWithSigner(txn=asset_create, signer=signer)]
        elif isinstance(txn, AppCallParams):
            app_call = self._build_app_call(txn, suggested_params)
            return [TransactionWithSigner(txn=app_call, signer=signer)]
        elif isinstance(txn, AssetConfigParams):
            asset_config = self._build_asset_config(txn, suggested_params)
            return [TransactionWithSigner(txn=asset_config, signer=signer)]
        elif isinstance(txn, AssetDestroyParams):
            asset_destroy = self._build_asset_destroy(txn, suggested_params)
            return [TransactionWithSigner(txn=asset_destroy, signer=signer)]
        elif isinstance(txn, AssetFreezeParams):
            asset_freeze = self._build_asset_freeze(txn, suggested_params)
            return [TransactionWithSigner(txn=asset_freeze, signer=signer)]
        elif isinstance(txn, AssetTransferParams):
            asset_transfer = self._build_asset_transfer(txn, suggested_params)
            return [TransactionWithSigner(txn=asset_transfer, signer=signer)]
        elif isinstance(txn, AssetOptInParams):
            asset_transfer = self._build_asset_transfer(
                AssetTransferParams(**txn.__dict__, receiver=txn.sender, amount=0), suggested_params
            )
            return [TransactionWithSigner(txn=asset_transfer, signer=signer)]
        elif isinstance(txn, AssetOptOutParams):
            asset_transfer = self._build_asset_transfer(
                AssetTransferParams(
                    **txn.__dict__,
                    receiver=txn.sender,
                    amount=0,
                    close_asset_to=txn.creator,
                ),
                suggested_params,
            )
            return [TransactionWithSigner(txn=asset_transfer, signer=signer)]
        elif isinstance(txn, OnlineKeyRegParams):
            key_reg = self._build_key_reg(txn, suggested_params)
            return [TransactionWithSigner(txn=key_reg, signer=signer)]
        else:
            raise ValueError(f"Unsupported txn: {txn}")

    def build_transactions(self) -> BuiltTransactions:
        suggested_params = self.get_suggested_params()

        transactions: list[Transaction] = []
        method_calls: dict[int, Method] = {}
        signers: dict[int, TransactionSigner] = {}

        idx = 0

        for txn in self.txns:
            txn_with_signers: list[TransactionWithSigner] = []

            if isinstance(
                txn,
                TransactionWithSigner
                | AtomicTransactionComposer
                | AppCallMethodCall
                | AppCreateMethodCall
                | AppUpdateMethodCall,
            ):
                txn_with_signers.extend(self._build_txn(txn, suggested_params))
            else:
                txn_with_signers.extend(self._build_txn(txn, suggested_params))

            for ts in txn_with_signers:
                transactions.append(ts.txn)
                if ts.signer and ts.signer != self.NULL_SIGNER:
                    signers[idx] = ts.signer
                method = self.txn_method_map.get(ts.txn.get_txid())
                if method:
                    method_calls[idx] = method
                idx += 1

        return BuiltTransactions(transactions=transactions, method_calls=method_calls, signers=signers)

    def count(self) -> int:
        return len(self.build_transactions().transactions)

    def build(self) -> dict[str, Any]:
        if self.atc.get_status() == algosdk.atomic_transaction_composer.AtomicTransactionComposerStatus.BUILDING:
            suggested_params = self.get_suggested_params()
            txn_with_signers: list[TransactionWithSigner] = []

            for txn in self.txns:
                txn_with_signers.extend(self._build_txn(txn, suggested_params))

            for ts in txn_with_signers:
                self.atc.add_transaction(ts)
                method = self.txn_method_map.get(ts.txn.get_txid())
                if method:
                    self.atc.method_dict[len(self.atc.txn_list) - 1] = method

        return {
            "atc": self.atc,
            "transactions": self.atc.build_group(),
            "method_calls": self.atc.method_dict,
        }

    def rebuild(self) -> dict[str, Any]:
        self.atc = AtomicTransactionComposer()
        return self.build()

    def _build_group(self) -> list[TransactionWithSigner]:
        suggested_params = self.get_suggested_params()

        txn_with_signers: list[TransactionWithSigner] = []

        for txn in self.txns:
            txn_with_signers.extend(self._build_txn(txn, suggested_params))

        for ts in txn_with_signers:
            self.atc.add_transaction(ts)

        method_calls = {}

        for i, ts in enumerate(txn_with_signers):
            method = self.txn_method_map.get(ts.txn.get_txid())
            if method:
                method_calls[i] = method

        self.atc.method_dict = method_calls

        return self.atc.build_group()

    @deprecated(reason="Use send() instead", version="3.0.0")
    def execute(
        self,
        *,
        max_rounds_to_wait: int | None = None,
    ) -> algosdk.atomic_transaction_composer.AtomicTransactionResponse:
        return self.send(
            max_rounds_to_wait=max_rounds_to_wait,
        )

    def send(
        self,
        max_rounds_to_wait: int | None = None,
    ) -> algosdk.atomic_transaction_composer.AtomicTransactionResponse:
        group = self.build()["transactions"]

        wait_rounds = max_rounds_to_wait
        if wait_rounds is None:
            last_round = max(txn.txn.last_valid_round for txn in group)
            first_round = self.get_suggested_params().first
            wait_rounds = last_round - first_round + 1

        try:
            return self.atc.execute(client=self.algod, wait_rounds=wait_rounds)  # TODO: reimplement ATC
        except algosdk.error.AlgodHTTPError as e:
            raise Exception(f"Transaction failed: {e}") from e

    def simulate(self) -> algosdk.atomic_transaction_composer.SimulateAtomicTransactionResponse:
        if config.debug and config.project_root and config.trace_all:
            return simulate_and_persist_response(
                self.atc,
                config.project_root,
                self.algod,
                config.trace_buffer_size_mb,
            )

        return simulate_response(
            self.atc,
            self.algod,
        )

    @staticmethod
    def arc2_note(dapp_name: str, format_type: str, data: str | dict[str, Any]) -> bytes:
        """
        Create an encoded transaction note that follows the ARC-2 spec.

        https://github.com/algorandfoundation/ARCs/blob/main/ARCs/arc-0002.md

        :param dapp_name: The name of the dApp.
        :param format_type: The format of the data ('j' for JSON, 't' for text).
        :param data: The data to include in the note.
        :return: The binary encoded transaction note.
        """
        if isinstance(data, dict):
            import json

            data_str = json.dumps(data)
        else:
            data_str = data

        arc2_payload = f"{dapp_name}:{format_type}{data_str}"
        return arc2_payload.encode("utf-8")
