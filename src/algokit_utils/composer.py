from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Union, cast

import algosdk
from algosdk.abi import ABIType, Method
from algosdk.atomic_transaction_composer import (AtomicTransactionComposer,
                                                 TransactionSigner,
                                                 TransactionWithSigner)
from algosdk.box_reference import BoxReference
from algosdk.transaction import OnComplete
from algosdk.v2client.algod import AlgodClient

AlgoAmount = int

@dataclass 
class SenderParam:
    sender: str

@dataclass
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
    signer: Optional[TransactionSigner] = None
    rekey_to: Optional[str] = None
    note: Optional[bytes] = None
    lease: Optional[bytes] = None
    static_fee: Optional[AlgoAmount] = None
    extra_fee: Optional[AlgoAmount] = None
    max_fee: Optional[AlgoAmount] = None
    validity_window: Optional[int] = None
    first_valid_round: Optional[int] = None
    last_valid_round: Optional[int] = None

@dataclass
class _RequiredPayTxnParams(SenderParam):
    receiver: str
    amount: AlgoAmount


@dataclass
class PayTxnParams(CommonTxnParams, _RequiredPayTxnParams):
    """
        Payment transaction parameters.

        :param receiver: The account that will receive the ALGO.
        :param amount: Amount to send.
        :param close_remainder_to: If given, close the sender account and send the remaining balance to this address.
        :param kwargs: Additional keyword arguments to pass to the parent class.
    """
    close_remainder_to: Optional[str] = None

@dataclass
class _RequiredAssetCreateParams(SenderParam):
    total: int

@dataclass
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
        :param kwargs: Additional keyword arguments to pass to the parent class.
    """
    decimals: Optional[int] = None
    default_frozen: Optional[bool] = None
    manager: Optional[str] = None
    reserve: Optional[str] = None
    freeze: Optional[str] = None
    clawback: Optional[str] = None
    unit_name: Optional[str] = None
    asset_name: Optional[str] = None
    url: Optional[str] = None
    metadata_hash: Optional[bytes] = None

@dataclass
class _RequiredAssetConfigParams(SenderParam):
    asset_id: int

@dataclass
class AssetConfigParams(CommonTxnParams, _RequiredAssetConfigParams):
    """
        Asset configuration parameters.

        :param asset_id: ID of the asset.
        :param manager: The address that can change the manager, reserve, clawback, and freeze addresses. There will permanently be no manager if undefined or an empty string.
        :param reserve: The address that holds the uncirculated supply.
        :param freeze: The address that can freeze the asset in any account. Freezing will be permanently disabled if undefined or an empty string.
        :param clawback: The address that can clawback the asset from any account. Clawback will be permanently disabled if undefined or an empty string.
        :param kwargs: Additional keyword arguments to pass to the parent class.
    """
    manager: Optional[str] = None
    reserve: Optional[str] = None
    freeze: Optional[str] = None
    clawback: Optional[str] = None


@dataclass
class _RequiredAssetFreezeParams(SenderParam):
    asset_id: int
    account: str
    frozen: bool

@dataclass
class AssetFreezeParams(CommonTxnParams, _RequiredAssetFreezeParams):
    """
        Asset freeze parameters.

        :param asset_id: The ID of the asset.
        :param account: The account to freeze or unfreeze.
        :param frozen: Whether the assets in the account should be frozen.
        :param kwargs: Additional keyword arguments to pass to the parent class.
    """
    pass

@dataclass
class _RequiredAssetDestroyParams(SenderParam):
    asset_id: int

@dataclass
class AssetDestroyParams(CommonTxnParams, _RequiredAssetDestroyParams):
    """
        Asset destruction parameters.

        :param asset_id: ID of the asset.
        :param kwargs: Additional keyword arguments to pass to the parent class.
    """
    pass

@dataclass
class _RequiredOnlineKeyRegParams(SenderParam):
    vote_key: bytes
    selection_key: bytes
    vote_first: int
    vote_last: int
    vote_key_dilution: int

@dataclass
class OnlineKeyRegParams(CommonTxnParams, _RequiredOnlineKeyRegParams):
    """
        Online key registration parameters.

        :param vote_key: The root participation public key.
        :param selection_key: The VRF public key.
        :param vote_first: The first round that the participation key is valid. Not to be confused with the `first_valid` round of the keyreg transaction.
        :param vote_last: The last round that the participation key is valid. Not to be confused with the `last_valid` round of the keyreg transaction.
        :param vote_key_dilution: This is the dilution for the 2-level participation key. It determines the interval (number of rounds) for generating new ephemeral keys.
        :param state_proof_key: The 64 byte state proof public key commitment.
        :param kwargs: Additional keyword arguments to pass to the parent class.
    """
    state_proof_key: Optional[bytes] = None

@dataclass
class _RequiredAssetTransferParams(SenderParam):
    asset_id: int
    amount: int
    receiver: str

@dataclass
class AssetTransferParams(CommonTxnParams, _RequiredAssetTransferParams):
    """
        Asset transfer parameters.

        :param asset_id: ID of the asset.
        :param amount: Amount of the asset to transfer (smallest divisible unit).
        :param receiver: The account to send the asset to.
        :param clawback_target: The account to take the asset from.
        :param close_asset_to: The account to close the asset to.
        :param kwargs: Additional keyword arguments to pass to the parent class.
    """
    clawback_target: Optional[str] = None
    close_asset_to: Optional[str] = None

@dataclass
class _RequiredAssetOptInParams(SenderParam):
    asset_id: int

@dataclass
class AssetOptInParams(CommonTxnParams, _RequiredAssetOptInParams):
    """
        Asset opt-in parameters.

        :param asset_id: ID of the asset.
        :param kwargs: Additional keyword arguments to pass to the parent class.
    """
    pass

@dataclass
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
        :param kwargs: Additional keyword arguments to pass to the parent class.
    """
    on_complete: Optional[OnComplete] = None
    app_id: Optional[int] = None
    approval_program: Optional[bytes] = None
    clear_program: Optional[bytes] = None
    schema: Optional[Dict[str, int]] = None
    args: Optional[List[bytes]] = None
    account_references: Optional[List[str]] = None
    app_references: Optional[List[int]] = None
    asset_references: Optional[List[int]] = None
    extra_pages: Optional[int] = None
    box_references: Optional[List[BoxReference]] = None

@dataclass
class _RequiredMethodCallParams(SenderParam):
    app_id: int
    method: Method

@dataclass
class MethodCallParams(CommonTxnParams, _RequiredMethodCallParams):
    """
        Method call parameters.

        :param app_id: ID of the application.
        :param method: The ABI method to call.
        :param args: Arguments to the ABI method.
        :param kwargs: Additional keyword arguments to pass to the parent class and AppCallParams.
    """
    args: Optional[List[Union[ABIType, 'Transaction']]] = None

Transaction = Union[
    PayTxnParams,
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

@dataclass
class PayTxn(PayTxnParams):
    type: str = 'pay'

@dataclass
class AssetCreateTxn(AssetCreateParams):
    type: str = 'assetCreate'

@dataclass
class AssetConfigTxn(AssetConfigParams):
    type: str = 'assetConfig'

@dataclass
class AssetFreezeTxn(AssetFreezeParams):
    type: str = 'assetFreeze'

@dataclass
class AssetDestroyTxn(AssetDestroyParams):
    type: str = 'assetDestroy'

@dataclass
class AssetTransferTxn(AssetTransferParams):
    type: str = 'assetTransfer'

@dataclass
class AssetOptInTxn(AssetOptInParams):
    type: str = 'assetOptIn'

@dataclass
class AppCallTxn(AppCallParams):
    type: str = 'appCall'

@dataclass
class OnlineKeyRegTxn(OnlineKeyRegParams):
    type: str = 'keyReg'

@dataclass
class TxnWithSigner:
    txn: TransactionWithSigner
    type: str = 'txnWithSigner'

@dataclass
class ATCTxn:
    atc: AtomicTransactionComposer
    type: str = 'atc'

@dataclass
class MethodCallTxn(MethodCallParams):
    type: str = 'methodCall'

Txn = Union[
    PayTxn,
    AssetCreateTxn,
    AssetConfigTxn,
    AssetFreezeTxn,
    AssetDestroyTxn,
    AssetTransferTxn,
    AssetOptInTxn,
    AppCallTxn,
    OnlineKeyRegTxn,
    TxnWithSigner,
    ATCTxn,
    MethodCallTxn,
]

class AlgokitComposer:
    """
    A class for composing and managing Algorand transactions using the Algosdk library.

    Attributes:
        txn_method_map (dict[str, algosdk.abi.Method]): A dictionary that maps transaction IDs to their corresponding ABI methods.
        txns (List[Txn]): A list of transactions that have not yet been composed.
        atc (AtomicTransactionComposer): An instance of AtomicTransactionComposer used to compose transactions.
        algod (AlgodClient): The AlgodClient instance used by the composer for suggested params.
        get_suggested_params (Callable[[], algosdk.future.transaction.SuggestedParams]): A function that returns suggested parameters for transactions.
        get_signer (Callable[[str], TransactionSigner]): A function that takes an address as input and returns a TransactionSigner for that address.
        default_validity_window (int): The default validity window for transactions.
    """

    def __init__(
        self,
        algod: AlgodClient,
        get_signer: Callable[[str], TransactionSigner],
        get_suggested_params: Optional[Callable[[], algosdk.transaction.SuggestedParams]] = None,
        default_validity_window: Optional[int] = None,
    ):
        """
        Initialize an instance of the AlgokitComposer class.

        Args:
            algod (AlgodClient): An instance of AlgodClient used to get suggested params and send transactions.
            get_signer (Callable[[str], TransactionSigner]): A function that takes an address as input and returns a TransactionSigner for that address.
            get_suggested_params (Optional[Callable[[], algosdk.future.transaction.SuggestedParams]], optional): A function that returns suggested parameters for transactions. If not provided, it defaults to using algod.suggested_params(). Defaults to None.
            default_validity_window (Optional[int], optional): The default validity window for transactions. If not provided, it defaults to 10. Defaults to None.
        """
        self.txn_method_map: dict[str, algosdk.abi.Method] = {}
        self.txns: List[Txn] = []
        self.atc: AtomicTransactionComposer = AtomicTransactionComposer()
        self.algod: AlgodClient = algod
        self.default_get_send_params = lambda: self.algod.suggested_params()
        self.get_suggested_params = get_suggested_params or self.default_get_send_params
        self.get_signer: Callable[[str], TransactionSigner] = get_signer
        self.default_validity_window: int = default_validity_window or 10

    def add_payment(self, params: PayTxnParams) -> 'AlgokitComposer':
        self.txns.append(PayTxn(**params.__dict__))
        return self

    def add_asset_create(self, params: AssetCreateParams) -> 'AlgokitComposer':
        self.txns.append(AssetCreateTxn(**params.__dict__))
        return self

    def add_asset_config(self, params: AssetConfigParams) -> 'AlgokitComposer':
        self.txns.append(AssetConfigTxn(**params.__dict__))
        return self

    def add_asset_freeze(self, params: AssetFreezeParams) -> 'AlgokitComposer':
        self.txns.append(AssetFreezeTxn(**params.__dict__))
        return self

    def add_asset_destroy(self, params: AssetDestroyParams) -> 'AlgokitComposer':
        self.txns.append(AssetDestroyTxn(**params.__dict__))
        return self

    def add_asset_transfer(self, params: AssetTransferParams) -> 'AlgokitComposer':
        self.txns.append(AssetTransferTxn(**params.__dict__))
        return self

    def add_asset_opt_in(self, params: AssetOptInParams) -> 'AlgokitComposer':
        self.txns.append(AssetOptInTxn(**params.__dict__))
        return self

    def add_app_call(self, params: AppCallParams) -> 'AlgokitComposer':
        self.txns.append(AppCallTxn(**params.__dict__))
        return self

    def add_online_key_reg(self, params: OnlineKeyRegParams) -> 'AlgokitComposer':
        self.txns.append(OnlineKeyRegTxn(**params.__dict__))
        return self

    def add_atc(self, atc: AtomicTransactionComposer) -> 'AlgokitComposer':
        self.txns.append(ATCTxn(atc=atc))
        return self

    def add_method_call(self, params: MethodCallParams) -> 'AlgokitComposer':
        self.txns.append(MethodCallTxn(**params.__dict__))
        return self
    
    def _build_atc(self, atc: AtomicTransactionComposer) -> List[TransactionWithSigner]:
        group = atc.build_group()

        for ts in group:
            ts.txn.group = None

        method = atc.method_dict.get(len(group) - 1)
        if method:
            self.txn_method_map[group[-1].txn.get_txid()] = method

        return group
    
    def _common_txn_build_step(self, params: CommonTxnParams, txn: algosdk.transaction.Transaction, suggested_params: algosdk.transaction.SuggestedParams) -> algosdk.transaction.Transaction:
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
            raise ValueError('Cannot set both static_fee and extra_fee')

        if params.static_fee is not None:
            txn.fee = params.static_fee
        else:
            txn.fee = txn.estimate_size() * suggested_params.fee or algosdk.constants.min_txn_fee
            if params.extra_fee:
                txn.fee += params.extra_fee

        if params.max_fee is not None and txn.fee > params.max_fee:
            raise ValueError(f'Transaction fee {txn.fee} is greater than max_fee {params.max_fee}')

        return txn
    
    def _build_payment(self, params: PayTxnParams, suggested_params: algosdk.transaction.SuggestedParams) -> algosdk.transaction.Transaction:
        txn = algosdk.transaction.PaymentTxn(
            sender=params.sender,
            sp=suggested_params,
            receiver=params.receiver,
            amt=params.amount,
            close_remainder_to=params.close_remainder_to,
        )

        return self._common_txn_build_step(params, txn, suggested_params)

    def _build_asset_create(self, params: AssetCreateParams, suggested_params: algosdk.transaction.SuggestedParams) -> algosdk.transaction.Transaction:
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
        )

        return self._common_txn_build_step(params, txn, suggested_params)

    def _build_app_call(self, params: AppCallParams, suggested_params: algosdk.transaction.SuggestedParams) -> algosdk.transaction.Transaction:
        sdk_params = {
            'sender': params.sender,
            'sp': suggested_params,
            'index': params.app_id or 0,
            'on_complete': params.on_complete or algosdk.transaction.OnComplete.NoOpOC,
            'approval_program': params.approval_program,
            'clear_program': params.clear_program,
            'app_args': params.args,
            'accounts': params.account_references,
            'foreign_apps': params.app_references,
            'foreign_assets': params.asset_references,
            'extra_pages': params.extra_pages,
            'local_schema': algosdk.transaction.StateSchema(num_uints=params.schema.get("local_uints") or 0, num_byte_slices=params.schema.get("local_byte_slices") or 0) if params.schema else None,
            'global_schema': algosdk.transaction.StateSchema(num_uints=params.schema.get("global_uints") or 0, num_byte_slices=params.schema.get("global_byte_slices") or 0) if params.schema else None,
        }

        if not params.app_id:
            if params.approval_program is None or params.clear_program is None:
                raise ValueError('approval_program and clear_program are required for application creation')

            txn = algosdk.transaction.ApplicationCreateTxn(**sdk_params)
        else:
            txn = algosdk.transaction.ApplicationCallTxn(**sdk_params)

        return self._common_txn_build_step(params, txn, suggested_params)

    def _build_asset_config(self, params: AssetConfigParams, suggested_params: algosdk.transaction.SuggestedParams) -> algosdk.transaction.Transaction:
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

    def _build_asset_destroy(self, params: AssetDestroyParams, suggested_params: algosdk.transaction.SuggestedParams) -> algosdk.transaction.Transaction:
        txn = algosdk.transaction.AssetDestroyTxn(
            sender=params.sender,
            sp=suggested_params,
            index=params.asset_id,
        )

        return self._common_txn_build_step(params, txn, suggested_params)

    def _build_asset_freeze(self, params: AssetFreezeParams, suggested_params: algosdk.transaction.SuggestedParams) -> algosdk.transaction.Transaction:
        txn = algosdk.transaction.AssetFreezeTxn(
            sender=params.sender,
            sp=suggested_params,
            index=params.asset_id,
            target=params.account,
            new_freeze_state=params.frozen,
        )

        return self._common_txn_build_step(params, txn, suggested_params)

    def _build_asset_transfer(self, params: AssetTransferParams, suggested_params: algosdk.transaction.SuggestedParams) -> algosdk.transaction.Transaction:
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

    def _build_key_reg(self, params: OnlineKeyRegParams, suggested_params: algosdk.transaction.SuggestedParams) -> algosdk.transaction.Transaction:
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
        

    def _build_method_call(self, params: MethodCallParams, suggested_params: algosdk.transaction.SuggestedParams) -> List[TransactionWithSigner]:
        method_args = []
        arg_offset = 0

        def is_abi_value(x) -> bool:
            if isinstance(x, list):
                return len(x) == 0 or all(is_abi_value(item) for item in x)

            return isinstance(x, (bool, int, float, str, bytes))

        if params.args:
            for i, arg in enumerate(params.args):
                if is_abi_value(arg):
                    method_args.append(arg)
                    continue

                if algosdk.abi.is_abi_transaction_type(params.method.args[i + arg_offset].type):
                    txn: Optional[algosdk.transaction.Transaction] = None
                    if isinstance(arg, MethodCallTxn):
                        temp_txn_with_signers = self._build_method_call(arg, suggested_params)
                        method_args.extend(temp_txn_with_signers)
                        arg_offset += len(temp_txn_with_signers) - 1
                        continue
                    elif isinstance(arg, AppCallTxn):
                        txn = self._build_app_call(arg, suggested_params)
                    elif isinstance(arg, PayTxn):
                        txn = self._build_payment(arg, suggested_params)
                    elif isinstance(arg, AssetOptInTxn):
                        txn = self._build_asset_transfer(AssetTransferParams(**arg.__dict__, receiver=arg.sender, amount=0), suggested_params)
                    elif isinstance(arg, AssetCreateTxn):
                        txn = self._build_asset_create(arg, suggested_params)
                    elif isinstance(arg, AssetConfigTxn):
                        txn = self._build_asset_config(arg, suggested_params)
                    elif isinstance(arg, AssetDestroyTxn):
                        txn = self._build_asset_destroy(arg, suggested_params)
                    elif isinstance(arg, AssetFreezeTxn):
                        txn = self._build_asset_freeze(arg, suggested_params)
                    elif isinstance(arg, AssetTransferTxn):
                        txn = self._build_asset_transfer(arg, suggested_params)
                    elif isinstance(arg, OnlineKeyRegTxn):
                        txn = self._build_key_reg(arg, suggested_params)
                    else:
                        raise ValueError(f'Unsupported method arg transaction type: {arg}')

                    method_args.append(TransactionWithSigner(txn=txn, signer=params.signer or self.get_signer(params.sender)))
                        
                    continue

                raise ValueError(f'Unsupported method arg: {arg}')

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
            lease=params.lease
        )

        return self._build_atc(method_atc)
    

    def _build_txn(self, txn: Txn, suggested_params: algosdk.transaction.SuggestedParams) -> List[TransactionWithSigner]:
        if isinstance(txn, TxnWithSigner):
            return [txn.txn]

        if isinstance(txn, ATCTxn):
            return self._build_atc(cast(ATCTxn, txn).atc)

        if isinstance(txn, MethodCallTxn):
            return self._build_method_call(txn, suggested_params)

        signer = txn.signer or self.get_signer(txn.sender)

        if isinstance(txn, PayTxn):
            payment = self._build_payment(txn, suggested_params)
            return [TransactionWithSigner(txn=payment, signer=signer)]
        elif isinstance(txn, AssetCreateTxn):
            asset_create = self._build_asset_create(txn, suggested_params)
            return [TransactionWithSigner(txn=asset_create, signer=signer)]
        elif isinstance(txn, AppCallTxn):
            app_call = self._build_app_call(txn, suggested_params)
            return [TransactionWithSigner(txn=app_call, signer=signer)]
        elif isinstance(txn, AssetConfigTxn):
            asset_config = self._build_asset_config(txn, suggested_params)
            return [TransactionWithSigner(txn=asset_config, signer=signer)]
        elif isinstance(txn, AssetDestroyTxn):
            asset_destroy = self._build_asset_destroy(txn, suggested_params)
            return [TransactionWithSigner(txn=asset_destroy, signer=signer)]
        elif isinstance(txn, AssetFreezeTxn):
            asset_freeze = self._build_asset_freeze(txn, suggested_params)
            return [TransactionWithSigner(txn=asset_freeze, signer=signer)]
        elif isinstance(txn, AssetTransferTxn):
            asset_transfer = self._build_asset_transfer(txn, suggested_params)
            return [TransactionWithSigner(txn=asset_transfer, signer=signer)]
        elif isinstance(txn, AssetOptInTxn):
            asset_transfer = self._build_asset_transfer(AssetTransferParams(**txn.__dict__, receiver=txn.sender, amount=0), suggested_params)
            return [TransactionWithSigner(txn=asset_transfer, signer=signer)]
        elif isinstance(txn, OnlineKeyRegTxn):
            key_reg = self._build_key_reg(txn, suggested_params)
            return [TransactionWithSigner(txn=key_reg, signer=signer)]
        else:
            raise ValueError(f'Unsupported txn type: {txn.type}')
        
    def build_group(self):
        suggested_params = self.get_suggested_params()

        txn_with_signers: List[TransactionWithSigner] = []

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

    def execute(self, *, max_rounds_to_wait: int | None = None):
        group = self.build_group()

        wait_rounds = max_rounds_to_wait

        if wait_rounds is None:
            last_round = max(txn.txn.last_valid_round for txn in group)
            first_round = self.get_suggested_params().first
            wait_rounds = last_round - first_round

        return self.atc.execute(client=self.algod, wait_rounds=wait_rounds)