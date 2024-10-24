from collections.abc import Callable
from dataclasses import dataclass
from typing import Union

import algosdk
from algosdk.abi import Method
from algosdk.atomic_transaction_composer import (
    AtomicTransactionComposer,
    AtomicTransactionResponse,
    TransactionSigner,
    TransactionWithSigner,
)
from algosdk.box_reference import BoxReference
from algosdk.transaction import OnComplete
from algosdk.v2client.algod import AlgodClient

from algokit_utils.applications.app_manager import AppManager


@dataclass(frozen=True)
class SenderParam:
    sender: str


@dataclass(frozen=True)
class CommonTxnParams:
    signer: TransactionSigner | None = None
    rekey_to: str | None = None
    note: bytes | None = None
    lease: bytes | None = None
    static_fee: int | None = None
    extra_fee: int | None = None
    max_fee: int | None = None
    validity_window: int | None = None
    first_valid_round: int | None = None
    last_valid_round: int | None = None


@dataclass(frozen=True)
class _RequiredPayTxnParams(SenderParam):
    receiver: str
    amount: int


@dataclass(frozen=True)
class PayParams(CommonTxnParams, _RequiredPayTxnParams):
    """
    Payment transaction parameters.

    :param receiver: The account that will receive the ALGO.
    :param amount: Amount to send.
    :param close_remainder_to: If given, close the sender account and send the remaining balance to this address.
    """

    close_remainder_to: str | None = None


@dataclass(frozen=True)
class _RequiredAssetCreateParams(SenderParam):
    total: int


@dataclass(frozen=True)
class AssetCreateParams(CommonTxnParams, _RequiredAssetCreateParams):
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
class AssetConfigParams(CommonTxnParams, _RequiredAssetConfigParams):
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
class AssetFreezeParams(CommonTxnParams, _RequiredAssetFreezeParams):
    """
    Asset freeze parameters.

    :param asset_id: The ID of the asset.
    :param account: The account to freeze or unfreeze.
    :param frozen: Whether the assets in the account should be frozen.
    """


@dataclass(frozen=True)
class _RequiredAssetDestroyParams(SenderParam):
    asset_id: int


@dataclass(frozen=True)
class AssetDestroyParams(CommonTxnParams, _RequiredAssetDestroyParams):
    """
    Asset destruction parameters.

    :param asset_id: ID of the asset.
    """


@dataclass(frozen=True)
class _RequiredOnlineKeyRegParams(SenderParam):
    vote_key: str
    selection_key: str
    vote_first: int
    vote_last: int
    vote_key_dilution: int


@dataclass(frozen=True)
class OnlineKeyRegParams(CommonTxnParams, _RequiredOnlineKeyRegParams):
    state_proof_key: bytes | None = None


@dataclass(frozen=True)
class _RequiredAssetTransferParams(SenderParam):
    asset_id: int
    amount: int
    receiver: str


@dataclass(frozen=True)
class AssetTransferParams(CommonTxnParams, _RequiredAssetTransferParams):
    clawback_target: str | None = None
    close_asset_to: str | None = None


@dataclass(frozen=True)
class _RequiredAssetOptInParams(SenderParam):
    asset_id: int


@dataclass(frozen=True)
class AssetOptInParams(CommonTxnParams, _RequiredAssetOptInParams):
    """
    Asset opt-in parameters.

    :param asset_id: ID of the asset.
    """


@dataclass(frozen=True)
class AppCallParams(CommonTxnParams, SenderParam):
    """
    Application call parameters.

    :param on_complete: The OnComplete action.
    :param app_id: ID of the application.
    :param approval_program: The program to execute for all OnCompletes other than ClearState.
    :param clear_program: The program to execute for ClearState OnComplete.
    :param schema: The state schema for the app. This is immutable.
    :param args: Application arguments.
    :param account_references: Account references.
    :param app_references: App references.
    :param asset_references: Asset references.
    :param extra_pages: Number of extra pages required for the programs.
    :param box_references: Box references.
    """

    on_complete: OnComplete | None = None
    app_id: int | None = None
    approval_program: bytes | None = None
    clear_program: bytes | None = None
    schema: dict[str, int] | None = None
    args: list[bytes] | None = None
    account_references: list[str] | None = None
    app_references: list[int] | None = None
    asset_references: list[int] | None = None
    extra_pages: int | None = None
    box_references: list[BoxReference] | None = None


@dataclass(frozen=True)
class _RequiredMethodCallParams(SenderParam):
    app_id: int
    method: Method


@dataclass(frozen=True)
class MethodCallParams(CommonTxnParams, _RequiredMethodCallParams):
    """
    Method call parameters.

    :param app_id: ID of the application.
    :param method: The ABI method to call.
    :param args: Arguments to the ABI method.
    """

    args: list | None = None


TxnParams = Union[  # noqa: UP007
    PayParams,
    AssetCreateParams,
    AssetConfigParams,
    AssetFreezeParams,
    AssetDestroyParams,
    OnlineKeyRegParams,
    AssetTransferParams,
    AssetOptInParams,
    AppCallParams,
    MethodCallParams,
]


class TransactionComposer:
    def __init__(  # noqa: PLR0913
        self,
        algod: AlgodClient,
        get_signer: Callable[[str], TransactionSigner],
        get_suggested_params: Callable[[], algosdk.transaction.SuggestedParams] | None = None,
        default_validity_window: int | None = None,
        app_manager: AppManager | None = None,
    ):
        self.txn_method_map: dict[str, algosdk.abi.Method] = {}
        self.txns: list[TransactionWithSigner | TxnParams | AtomicTransactionComposer] = []
        self.atc: AtomicTransactionComposer = AtomicTransactionComposer()
        self.algod: AlgodClient = algod
        self.default_get_send_params = lambda: self.algod.suggested_params()
        self.get_suggested_params = get_suggested_params or self.default_get_send_params
        self.get_signer: Callable[[str], TransactionSigner] = get_signer
        self.default_validity_window: int = default_validity_window or 10
        # TODO: Update composer to match latest interface and use the app manager
        self.app_manager: AppManager | None = app_manager or AppManager(algod)

    def add_payment(self, params: PayParams) -> "TransactionComposer":
        self.txns.append(params)
        return self

    def add_asset_create(self, params: AssetCreateParams) -> "TransactionComposer":
        self.txns.append(params)
        return self

    def add_asset_config(self, params: AssetConfigParams) -> "TransactionComposer":
        self.txns.append(params)
        return self

    def add_asset_freeze(self, params: AssetFreezeParams) -> "TransactionComposer":
        self.txns.append(params)
        return self

    def add_asset_destroy(self, params: AssetDestroyParams) -> "TransactionComposer":
        self.txns.append(params)
        return self

    def add_asset_transfer(self, params: AssetTransferParams) -> "TransactionComposer":
        self.txns.append(params)
        return self

    def add_asset_opt_in(self, params: AssetOptInParams) -> "TransactionComposer":
        self.txns.append(params)
        return self

    def add_app_call(self, params: AppCallParams) -> "TransactionComposer":
        self.txns.append(params)
        return self

    def add_online_key_reg(self, params: OnlineKeyRegParams) -> "TransactionComposer":
        self.txns.append(params)
        return self

    def add_atc(self, atc: AtomicTransactionComposer) -> "TransactionComposer":
        self.txns.append(atc)
        return self

    def add_method_call(self, params: MethodCallParams) -> "TransactionComposer":
        self.txns.append(params)
        return self

    def _build_atc(self, atc: AtomicTransactionComposer) -> list[TransactionWithSigner]:
        group = atc.build_group()

        for ts in group:
            ts.txn.group = None

        method = atc.method_dict.get(len(group) - 1)
        if method:
            self.txn_method_map[group[-1].txn.get_txid()] = method

        return group

    def _common_txn_build_step(
        self,
        params: CommonTxnParams,
        txn: algosdk.transaction.Transaction,
        suggested_params: algosdk.transaction.SuggestedParams,
    ) -> algosdk.transaction.Transaction:
        if params.lease:
            txn.lease = params.lease
        if params.rekey_to:
            txn.rekey_to = algosdk.encoding.decode_address(params.rekey_to)
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
            txn.fee = txn.estimate_size() * suggested_params.fee or algosdk.constants.min_txn_fee
            if params.extra_fee:
                txn.fee += params.extra_fee

        if params.max_fee is not None and txn.fee > params.max_fee:
            raise ValueError(f"Transaction fee {txn.fee} is greater than max_fee {params.max_fee}")

        return txn

    def _build_payment(
        self, params: PayParams, suggested_params: algosdk.transaction.SuggestedParams
    ) -> algosdk.transaction.Transaction:
        txn = algosdk.transaction.PaymentTxn(
            sender=params.sender,
            sp=suggested_params,
            receiver=params.receiver,
            amt=params.amount,
            close_remainder_to=params.close_remainder_to,
        )

        return self._common_txn_build_step(params, txn, suggested_params)

    def _build_asset_create(
        self, params: AssetCreateParams, suggested_params: algosdk.transaction.SuggestedParams
    ) -> algosdk.transaction.Transaction:
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

    def _build_app_call(
        self, params: AppCallParams, suggested_params: algosdk.transaction.SuggestedParams
    ) -> algosdk.transaction.Transaction:
        sdk_params = {
            "sender": params.sender,
            "sp": suggested_params,
            "index": params.app_id or 0,
            "on_complete": params.on_complete or algosdk.transaction.OnComplete.NoOpOC,
            "approval_program": params.approval_program,
            "clear_program": params.clear_program,
            "app_args": params.args,
            "accounts": params.account_references,
            "foreign_apps": params.app_references,
            "foreign_assets": params.asset_references,
            "extra_pages": params.extra_pages,
            "local_schema": algosdk.transaction.StateSchema(
                num_uints=params.schema.get("local_uints", 0), num_byte_slices=params.schema.get("local_byte_slices", 0)
            )
            if params.schema
            else None,
            "global_schema": algosdk.transaction.StateSchema(
                num_uints=params.schema.get("global_uints", 0),
                num_byte_slices=params.schema.get("global_byte_slices", 0),
            )
            if params.schema
            else None,
        }

        if not params.app_id:
            if params.approval_program is None or params.clear_program is None:
                raise ValueError("approval_program and clear_program are required for application creation")

            txn = algosdk.transaction.ApplicationCreateTxn(**sdk_params)
        else:
            txn = algosdk.transaction.ApplicationCallTxn(**sdk_params)  # type: ignore[assignment]

        return self._common_txn_build_step(params, txn, suggested_params)

    def _build_asset_config(
        self, params: AssetConfigParams, suggested_params: algosdk.transaction.SuggestedParams
    ) -> algosdk.transaction.Transaction:
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

    def _build_asset_destroy(
        self, params: AssetDestroyParams, suggested_params: algosdk.transaction.SuggestedParams
    ) -> algosdk.transaction.Transaction:
        txn = algosdk.transaction.AssetDestroyTxn(
            sender=params.sender,
            sp=suggested_params,
            index=params.asset_id,
        )

        return self._common_txn_build_step(params, txn, suggested_params)

    def _build_asset_freeze(
        self, params: AssetFreezeParams, suggested_params: algosdk.transaction.SuggestedParams
    ) -> algosdk.transaction.Transaction:
        txn = algosdk.transaction.AssetFreezeTxn(
            sender=params.sender,
            sp=suggested_params,
            index=params.asset_id,
            target=params.account,
            new_freeze_state=params.frozen,
        )

        return self._common_txn_build_step(params, txn, suggested_params)

    def _build_asset_transfer(
        self, params: AssetTransferParams, suggested_params: algosdk.transaction.SuggestedParams
    ) -> algosdk.transaction.Transaction:
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

    def _build_key_reg(
        self, params: OnlineKeyRegParams, suggested_params: algosdk.transaction.SuggestedParams
    ) -> algosdk.transaction.Transaction:
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

    def _is_abi_value(self, x: bool | float | str | bytes | list | TxnParams) -> bool:
        if isinstance(x, list):
            return len(x) == 0 or all(self._is_abi_value(item) for item in x)

        return isinstance(x, bool | int | float | str | bytes)

    def _build_method_call(  # noqa: C901, PLR0912
        self, params: MethodCallParams, suggested_params: algosdk.transaction.SuggestedParams
    ) -> list[TransactionWithSigner]:
        method_args = []
        arg_offset = 0

        if params.args:
            for i, arg in enumerate(params.args):
                if self._is_abi_value(arg):
                    method_args.append(arg)
                    continue

                if algosdk.abi.is_abi_transaction_type(params.method.args[i + arg_offset].type):
                    match arg:
                        case MethodCallParams():
                            temp_txn_with_signers = self._build_method_call(arg, suggested_params)
                            method_args.extend(temp_txn_with_signers)
                            arg_offset += len(temp_txn_with_signers) - 1
                            continue
                        case AppCallParams():
                            txn = self._build_app_call(arg, suggested_params)
                        case PayParams():
                            txn = self._build_payment(arg, suggested_params)
                        case AssetOptInParams():
                            txn = self._build_asset_transfer(
                                AssetTransferParams(**arg.__dict__, receiver=arg.sender, amount=0), suggested_params
                            )
                        case AssetCreateParams():
                            txn = self._build_asset_create(arg, suggested_params)
                        case AssetConfigParams():
                            txn = self._build_asset_config(arg, suggested_params)
                        case AssetDestroyParams():
                            txn = self._build_asset_destroy(arg, suggested_params)
                        case AssetFreezeParams():
                            txn = self._build_asset_freeze(arg, suggested_params)
                        case AssetTransferParams():
                            txn = self._build_asset_transfer(arg, suggested_params)
                        case OnlineKeyRegParams():
                            txn = self._build_key_reg(arg, suggested_params)
                        case _:
                            raise ValueError(f"Unsupported method arg transaction type: {arg}")

                    method_args.append(
                        TransactionWithSigner(txn=txn, signer=params.signer or self.get_signer(params.sender))
                    )

                    continue

                raise ValueError(f"Unsupported method arg: {arg}")

        method_atc = AtomicTransactionComposer()

        method_atc.add_method_call(
            app_id=params.app_id or 0,
            method=params.method,
            sender=params.sender,
            sp=suggested_params,
            signer=params.signer or self.get_signer(params.sender),
            method_args=method_args,
            on_complete=algosdk.transaction.OnComplete.NoOpOC,
            note=params.note,
            lease=params.lease,
        )

        return self._build_atc(method_atc)

    def _build_txn(  # noqa: C901, PLR0912, PLR0911
        self,
        txn: TransactionWithSigner | TxnParams | AtomicTransactionComposer,
        suggested_params: algosdk.transaction.SuggestedParams,
    ) -> list[TransactionWithSigner]:
        match txn:
            case TransactionWithSigner():
                return [txn]
            case AtomicTransactionComposer():
                return self._build_atc(txn)
            case MethodCallParams():
                return self._build_method_call(txn, suggested_params)

        signer = txn.signer or self.get_signer(txn.sender)

        match txn:
            case PayParams():
                payment = self._build_payment(txn, suggested_params)
                return [TransactionWithSigner(txn=payment, signer=signer)]
            case AssetCreateParams():
                asset_create = self._build_asset_create(txn, suggested_params)
                return [TransactionWithSigner(txn=asset_create, signer=signer)]
            case AppCallParams():
                app_call = self._build_app_call(txn, suggested_params)
                return [TransactionWithSigner(txn=app_call, signer=signer)]
            case AssetConfigParams():
                asset_config = self._build_asset_config(txn, suggested_params)
                return [TransactionWithSigner(txn=asset_config, signer=signer)]
            case AssetDestroyParams():
                asset_destroy = self._build_asset_destroy(txn, suggested_params)
                return [TransactionWithSigner(txn=asset_destroy, signer=signer)]
            case AssetFreezeParams():
                asset_freeze = self._build_asset_freeze(txn, suggested_params)
                return [TransactionWithSigner(txn=asset_freeze, signer=signer)]
            case AssetTransferParams():
                asset_transfer = self._build_asset_transfer(txn, suggested_params)
                return [TransactionWithSigner(txn=asset_transfer, signer=signer)]
            case AssetOptInParams():
                asset_transfer = self._build_asset_transfer(
                    AssetTransferParams(**txn.__dict__, receiver=txn.sender, amount=0), suggested_params
                )
                return [TransactionWithSigner(txn=asset_transfer, signer=signer)]
            case OnlineKeyRegParams():
                key_reg = self._build_key_reg(txn, suggested_params)
                return [TransactionWithSigner(txn=key_reg, signer=signer)]
            case _:
                raise ValueError(f"Unsupported txn: {txn}")

    def build_group(self) -> list[TransactionWithSigner]:
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

    def execute(self, *, max_rounds_to_wait: int | None = None) -> AtomicTransactionResponse:
        group = self.build_group()

        wait_rounds = max_rounds_to_wait

        if wait_rounds is None:
            last_round = max(txn.txn.last_valid_round for txn in group)
            first_round = self.get_suggested_params().first
            wait_rounds = last_round - first_round

        return self.atc.execute(client=self.algod, wait_rounds=wait_rounds)
