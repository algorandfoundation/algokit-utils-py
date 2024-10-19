from collections.abc import Callable
from dataclasses import dataclass
from typing import (
    Any,
)

import algosdk
from algosdk import atomic_transaction_composer, encoding
from algosdk.abi import Method
from algosdk.atomic_transaction_composer import (
    AtomicTransactionComposer,
    AtomicTransactionResponse,
    EmptySigner,
    SimulateAtomicTransactionResponse,
    TransactionSigner,
    TransactionWithSigner,
)
from algosdk.box_reference import BoxReference
from algosdk.constants import MIN_TXN_FEE
from algosdk.error import AlgodHTTPError
from algosdk.transaction import (
    OnComplete,
    SuggestedParams,
    Transaction,
)
from algosdk.v2client.algod import AlgodClient
from algosdk.v2client.models import SimulateRequest, SimulateRequestTransactionGroup, SimulateTraceConfig


@dataclass(frozen=True)
class SenderParam:
    sender: str


@dataclass(frozen=True)
class CommonTxnParams:
    """
    Common transaction parameters.

    :param signer: The function used to sign transactions.
    :param rekey_to: Change the signing key of the sender to the given address.
    :param note: Note to attach to the transaction.
    :param lease: Prevent multiple transactions with the same lease being included within the validity window.
    :param static_fee: The transaction fee. In most cases you want to use `extra_fee` unless setting the fee to 0 to be covered by another transaction.
    :param extra_fee: The fee to pay IN ADDITION to the suggested fee. Useful for covering inner transaction fees.
    :param max_fee: Throw an error if the fee for the transaction is more than this amount.
    :param validity_window: How many rounds the transaction should be valid for.
    :param first_valid_round: Set the first round this transaction is valid. If left undefined, the value from algod will be used. Only set this when you intentionally want this to be some time in the future.
    :param last_valid_round: The last round this transaction is valid. It is recommended to use validity_window instead.
    """

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
class _RequiredPaymentTxnParams(SenderParam):
    receiver: str
    amount: int


@dataclass(frozen=True)
class PaymentParams(CommonTxnParams, _RequiredPaymentTxnParams):
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
    """
    Asset creation parameters.

    :param total: The total amount of the smallest divisible unit to create.
    :param decimals: The amount of decimal places the asset should have.
    :param default_frozen: Whether the asset is frozen by default in the creator address.
    :param manager: The address that can change the manager, reserve, clawback, and freeze addresses. There will permanently be no manager if undefined or an empty string.
    :param reserve: The address that holds the uncirculated supply.
    :param freeze: The address that can freeze the asset in any account. Freezing will be permanently disabled if undefined or an empty string.
    :param clawback: The address that can clawback the asset from any account. Clawback will be permanently disabled if undefined or an empty string.
    :param unit_name: The short ticker name for the asset.
    :param asset_name: The full name of the asset.
    :param url: The metadata URL for the asset.
    :param metadata_hash: Hash of the metadata contained in the metadata URL.
    """

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
    """
    Asset configuration parameters.

    :param asset_id: ID of the asset.
    :param manager: The address that can change the manager, reserve, clawback, and freeze addresses. There will permanently be no manager if undefined or an empty string.
    :param reserve: The address that holds the uncirculated supply.
    :param freeze: The address that can freeze the asset in any account. Freezing will be permanently disabled if undefined or an empty string.
    :param clawback: The address that can clawback the asset from any account. Clawback will be permanently disabled if undefined or an empty string.
    """

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
    """
    Online key registration parameters.

    :param vote_key: The root participation public key.
    :param selection_key: The VRF public key.
    :param vote_first: The first round that the participation key is valid. Not to be confused with the `first_valid` round of the keyreg transaction.
    :param vote_last: The last round that the participation key is valid. Not to be confused with the `last_valid` round of the keyreg transaction.
    :param vote_key_dilution: This is the dilution for the 2-level participation key. It determines the interval (number of rounds) for generating new ephemeral keys.
    :param state_proof_key: The 64 byte state proof public key commitment.
    """

    state_proof_key: bytes | None = None


@dataclass(frozen=True)
class _RequiredAssetTransferParams(SenderParam):
    asset_id: int
    amount: int
    receiver: str


@dataclass(frozen=True)
class AssetTransferParams(CommonTxnParams, _RequiredAssetTransferParams):
    """
    Asset transfer parameters.

    :param asset_id: ID of the asset.
    :param amount: Amount of the asset to transfer (smallest divisible unit).
    :param receiver: The account to send the asset to.
    :param clawback_target: The account to take the asset from.
    :param close_asset_to: The account to close the asset to.
    """

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
class _RequiredAssetOptOutParams(SenderParam):
    asset_id: int
    creator: str


@dataclass(frozen=True)
class AssetOptOutParams(CommonTxnParams, _RequiredAssetOptOutParams):
    """
    Asset opt-out parameters.

    :param asset_id: ID of the asset.
    :param creator: The address of the asset creator to close the asset to.
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

    args: list[Any] | None = None  # Arguments can be various types


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
    | MethodCallParams
)


@dataclass
class BuiltTransactions:
    """
    Set of transactions built by AlgokitComposer.

    :param transactions: The built transactions.
    :param method_calls: Any ABIMethod objects associated with any of the transactions in a map keyed by transaction index.
    :param signers: Any TransactionSigner objects associated with any of the transactions in a map keyed by transaction index.
    """

    transactions: list[Transaction]
    method_calls: dict[int, Method]
    signers: dict[int, TransactionSigner]


class AlgokitComposer:
    """
    A class for composing and managing Algorand transactions using the Algosdk library.

    Attributes:
        txn_method_map (dict[str, algosdk.abi.Method]): A dictionary that maps transaction IDs to their corresponding ABI methods.
        txns (List[Union[TransactionWithSigner, TxnParams, AtomicTransactionComposer]]): A list of transactions that have not yet been composed.
        atc (AtomicTransactionComposer): An instance of AtomicTransactionComposer used to compose transactions.
        algod (AlgodClient): The AlgodClient instance used by the composer for suggested params.
        get_suggested_params (Callable[[], algosdk.transaction.SuggestedParams]): A function that returns suggested parameters for transactions.
        get_signer (Callable[[str], TransactionSigner]): A function that takes an address as input and returns a TransactionSigner for that address.
        default_validity_window (int): The default validity window for transactions.
    """

    NULL_SIGNER = EmptySigner()

    def __init__(
        self,
        algod: AlgodClient,
        get_signer: Callable[[str], TransactionSigner],
        get_suggested_params: Callable[[], SuggestedParams] | None = None,
        default_validity_window: int | None = None,
    ):
        """
        Initialize an instance of the AlgokitComposer class.

        Args:
            algod (AlgodClient): An instance of AlgodClient used to get suggested params and send transactions.
            get_signer (Callable[[str], TransactionSigner]): A function that takes an address as input and returns a TransactionSigner for that address.
            get_suggested_params (Optional[Callable[[], algosdk.future.transaction.SuggestedParams]], optional): A function that returns suggested parameters for transactions. If not provided, it defaults to using algod.suggested_params(). Defaults to None.
            default_validity_window (Optional[int], optional): The default validity window for transactions. If not provided, it defaults to 10. Defaults to None.
        """
        self.txn_method_map: dict[str, Method] = {}
        self.txns: list[TransactionWithSigner | TxnParams | AtomicTransactionComposer] = []
        self.atc: AtomicTransactionComposer = AtomicTransactionComposer()
        self.algod: AlgodClient = algod
        self.get_suggested_params = get_suggested_params or algod.suggested_params
        self.get_signer: Callable[[str], TransactionSigner] = get_signer
        self.default_validity_window: int = default_validity_window or 10
        self.default_validity_window_is_explicit = default_validity_window is not None

    def add_payment(self, params: PaymentParams) -> "AlgokitComposer":
        self.txns.append(params)
        return self

    def add_asset_create(self, params: AssetCreateParams) -> "AlgokitComposer":
        self.txns.append(params)
        return self

    def add_asset_config(self, params: AssetConfigParams) -> "AlgokitComposer":
        self.txns.append(params)
        return self

    def add_asset_freeze(self, params: AssetFreezeParams) -> "AlgokitComposer":
        self.txns.append(params)
        return self

    def add_asset_destroy(self, params: AssetDestroyParams) -> "AlgokitComposer":
        self.txns.append(params)
        return self

    def add_asset_transfer(self, params: AssetTransferParams) -> "AlgokitComposer":
        self.txns.append(params)
        return self

    def add_asset_opt_in(self, params: AssetOptInParams) -> "AlgokitComposer":
        self.txns.append(params)
        return self

    def add_asset_opt_out(self, params: AssetOptOutParams) -> "AlgokitComposer":
        self.txns.append(params)
        return self

    def add_app_call(self, params: AppCallParams) -> "AlgokitComposer":
        self.txns.append(params)
        return self

    def add_online_key_reg(self, params: OnlineKeyRegParams) -> "AlgokitComposer":
        self.txns.append(params)
        return self

    def add_method_call(self, params: MethodCallParams) -> "AlgokitComposer":
        self.txns.append(params)
        return self

    def add_atc(self, atc: AtomicTransactionComposer) -> "AlgokitComposer":
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
                self.txn_method_map[ts.txn.get_txid()] = method  # type: ignore[no-untyped-call]
            txn_with_signers.append(ts)

        return txn_with_signers

    def _common_txn_build_step(
        self,
        params: CommonTxnParams,
        txn: Transaction,
        suggested_params: SuggestedParams,
    ) -> Transaction:
        if params.lease:
            txn.lease = params.lease
        if params.rekey_to:
            txn.rekey_to = encoding.decode_address(params.rekey_to)  # type: ignore[no-untyped-call]
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
                txn.fee += params.extra_fee

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
        )  # type: ignore[no-untyped-call]

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
        )  # type: ignore[no-untyped-call]

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
        )  # type: ignore[no-untyped-call]

        return self._common_txn_build_step(params, txn, suggested_params)

    def _build_asset_destroy(self, params: AssetDestroyParams, suggested_params: SuggestedParams) -> Transaction:
        txn = algosdk.transaction.AssetDestroyTxn(
            sender=params.sender,
            sp=suggested_params,
            index=params.asset_id,
        )  # type: ignore[no-untyped-call]

        return self._common_txn_build_step(params, txn, suggested_params)

    def _build_asset_freeze(self, params: AssetFreezeParams, suggested_params: SuggestedParams) -> Transaction:
        txn = algosdk.transaction.AssetFreezeTxn(
            sender=params.sender,
            sp=suggested_params,
            index=params.asset_id,
            target=params.account,
            new_freeze_state=params.frozen,
        )  # type: ignore[no-untyped-call]

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
        )  # type: ignore[no-untyped-call]

        return self._common_txn_build_step(params, txn, suggested_params)

    def _build_app_call(self, params: AppCallParams, suggested_params: SuggestedParams) -> Transaction:
        sdk_params = {
            "sender": params.sender,
            "sp": suggested_params,
            "index": params.app_id or 0,
            "on_complete": params.on_complete or OnComplete.NoOpOC,
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

            txn = algosdk.transaction.ApplicationCreateTxn(**sdk_params)  # type: ignore[no-untyped-call]
        else:
            txn = algosdk.transaction.ApplicationCallTxn(**sdk_params)  # type: ignore[assignment,no-untyped-call]

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
        )  # type: ignore[no-untyped-call]

        return self._common_txn_build_step(params, txn, suggested_params)

    def _is_abi_value(self, x: bool | float | str | bytes | list | TxnParams) -> bool:
        if isinstance(x, list):
            return len(x) == 0 or all(self._is_abi_value(item) for item in x)

        return isinstance(x, bool | int | float | str | bytes)

    def _build_method_call(
        self,
        params: MethodCallParams,
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
                    if isinstance(arg, MethodCallParams):
                        temp_txn_with_signers = self._build_method_call(arg, suggested_params, include_signer)
                        method_args.extend(temp_txn_with_signers)
                        arg_offset += len(temp_txn_with_signers) - 1
                        continue
                    elif isinstance(arg, AppCallParams):
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

                    signer = arg.signer or self.get_signer(arg.sender) if include_signer else self.NULL_SIGNER
                    method_args.append(TransactionWithSigner(txn=txn, signer=signer))

                    continue

                raise ValueError(f"Unsupported method arg: {arg}")

        method_atc = AtomicTransactionComposer()

        method_atc.add_method_call(
            app_id=params.app_id or 0,
            method=params.method,
            sender=params.sender,
            sp=suggested_params,
            signer=params.signer or self.get_signer(params.sender) if include_signer else self.NULL_SIGNER,
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

    def _build_txn(
        self,
        txn: TransactionWithSigner | TxnParams | AtomicTransactionComposer,
        suggested_params: SuggestedParams,
    ) -> list[TransactionWithSigner]:
        if isinstance(txn, TransactionWithSigner):
            return [txn]

        if isinstance(txn, AtomicTransactionComposer):
            return self._build_atc(txn)

        if isinstance(txn, MethodCallParams):
            return self._build_method_call(txn, suggested_params, include_signer=True)

        signer = txn.signer or self.get_signer(txn.sender)

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

            if isinstance(txn, TransactionWithSigner | AtomicTransactionComposer | MethodCallParams):
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
        if self.atc.get_status() == atomic_transaction_composer.AtomicTransactionComposerStatus.BUILDING:
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
            method = self.txn_method_map.get(ts.txn.get_txid())  # type: ignore[no-untyped-call]
            if method:
                method_calls[i] = method

        self.atc.method_dict = method_calls

        return self.atc.build_group()

    def execute(self, *, max_rounds_to_wait: int | None = None) -> AtomicTransactionResponse:
        group = self._build_group()

        wait_rounds = max_rounds_to_wait

        if wait_rounds is None:
            last_round = max(txn.txn.last_valid_round for txn in group)
            first_round = self.get_suggested_params().first
            wait_rounds = last_round - first_round

        return self.atc.execute(client=self.algod, wait_rounds=wait_rounds)

    def send(self, max_rounds_to_wait: int | None = None) -> AtomicTransactionResponse:
        group = self.build()["transactions"]

        wait_rounds = max_rounds_to_wait
        if wait_rounds is None:
            last_round = max(txn.txn.last_valid_round for txn in group)
            first_round = self.get_suggested_params().first
            wait_rounds = last_round - first_round + 1

        try:
            return self.atc.execute(client=self.algod, wait_rounds=wait_rounds)
        except AlgodHTTPError as e:
            raise Exception(f"Transaction failed: {e}")

    def simulate(self) -> SimulateAtomicTransactionResponse:
        unsigned_txn_groups = self.atc.build_group()
        empty_signer = EmptySigner()
        txn_list = [txn_group.txn for txn_group in unsigned_txn_groups]
        fake_signed_transactions = empty_signer.sign_transactions(txn_list, [])
        txn_group = [SimulateRequestTransactionGroup(txns=fake_signed_transactions)]
        trace_config = SimulateTraceConfig(enable=True, stack_change=True, scratch_change=True)

        simulate_request = SimulateRequest(
            txn_groups=txn_group, allow_more_logs=True, allow_empty_signatures=True, exec_trace_config=trace_config
        )

        try:
            return self.atc.simulate(self.algod, simulate_request)
        except AlgodHTTPError as e:
            raise Exception(f"Simulation failed: {e}")

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
