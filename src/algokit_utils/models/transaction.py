from dataclasses import dataclass
from typing import Any, Generic, Literal, TypedDict, TypeVar, cast

import algosdk
from typing_extensions import Self

from algokit_utils.models.abi import ABIReturn


# Define specific types for different formats
class BaseArc2Note(TypedDict):
    """Base ARC-0002 transaction note structure"""

    dapp_name: str


class StringFormatArc2Note(BaseArc2Note):
    """ARC-0002 note for string-based formats (m/b/u)"""

    format: Literal["m", "b", "u"]
    data: str


class JsonFormatArc2Note(BaseArc2Note):
    """ARC-0002 note for JSON format"""

    format: Literal["j"]
    data: str | dict[str, Any] | list[Any] | int | None


# Combined type for all valid ARC-0002 notes
# See: https://github.com/algorandfoundation/ARCs/blob/main/ARCs/arc-0002.md
Arc2TransactionNote = StringFormatArc2Note | JsonFormatArc2Note

TransactionNoteData = str | None | int | list[Any] | dict[str, Any]
TransactionNote = bytes | TransactionNoteData | Arc2TransactionNote

T = TypeVar("T")


class TransactionWrapper(algosdk.transaction.Transaction):
    """Wrapper around algosdk.transaction.Transaction with optional property validators"""

    def __init__(self, transaction: algosdk.transaction.Transaction) -> None:
        self._raw = transaction

    @property
    def raw(self) -> algosdk.transaction.Transaction:
        return self._raw

    @property
    def payment(self) -> algosdk.transaction.PaymentTxn | None:
        return self._return_if_type(
            algosdk.transaction.PaymentTxn,
        )

    @property
    def keyreg(self) -> algosdk.transaction.KeyregTxn | None:
        return self._return_if_type(algosdk.transaction.KeyregTxn)

    @property
    def asset_config(self) -> algosdk.transaction.AssetConfigTxn | None:
        return self._return_if_type(algosdk.transaction.AssetConfigTxn)

    @property
    def asset_transfer(self) -> algosdk.transaction.AssetTransferTxn | None:
        return self._return_if_type(algosdk.transaction.AssetTransferTxn)

    @property
    def asset_freeze(self) -> algosdk.transaction.AssetFreezeTxn | None:
        return self._return_if_type(algosdk.transaction.AssetFreezeTxn)

    @property
    def application_call(self) -> algosdk.transaction.ApplicationCallTxn | None:
        return self._return_if_type(algosdk.transaction.ApplicationCallTxn)

    @property
    def state_proof(self) -> algosdk.transaction.StateProofTxn | None:
        return self._return_if_type(algosdk.transaction.StateProofTxn)

    def _return_if_type(self, txn_type: type[T]) -> T | None:
        if isinstance(self._raw, txn_type):
            return cast(T, self._raw)
        return None


@dataclass(kw_only=True, frozen=True)
class SendParams:
    max_rounds_to_wait: int | None = None
    suppress_log: bool | None = None
    populate_app_call_resources: bool | None = None


@dataclass
class SendAtomicTransactionComposerResults:
    """Results from sending an AtomicTransactionComposer transaction group"""

    group_id: str
    """The group ID if this was a transaction group"""
    confirmations: list[algosdk.v2client.algod.AlgodResponseType]
    """The confirmation info for each transaction"""
    tx_ids: list[str]
    """The transaction IDs that were sent"""
    transactions: list[TransactionWrapper]
    """The transactions that were sent"""
    returns: list[ABIReturn]
    """The ABI return values from any ABI method calls"""
    simulate_response: dict[str, Any] | None = None


@dataclass(frozen=True, kw_only=True)
class SendSingleTransactionResult:
    transaction: TransactionWrapper  # Last transaction
    confirmation: algosdk.v2client.algod.AlgodResponseType  # Last confirmation

    # Fields from SendAtomicTransactionComposerResults
    group_id: str
    tx_id: str | None = None
    tx_ids: list[str]  # Full array of transaction IDs
    transactions: list[TransactionWrapper]
    confirmations: list[algosdk.v2client.algod.AlgodResponseType]
    returns: list[ABIReturn] | None = None

    @classmethod
    def from_composer_result(cls, result: SendAtomicTransactionComposerResults, index: int = -1) -> Self:
        # Get base parameters
        base_params = {
            "transaction": TransactionWrapper(result.transactions[index]),
            "confirmation": result.confirmations[index],
            "group_id": result.group_id,
            "tx_id": result.tx_ids[index],
            "tx_ids": result.tx_ids,
            "transactions": result.transactions,
            "confirmations": result.confirmations,
            "returns": result.returns,
        }

        # For asset creation, extract asset_id from confirmation
        if cls is SendSingleAssetCreateTransactionResult:
            base_params["asset_id"] = result.confirmations[index]["asset-index"]  # type: ignore[index]
        # For app creation, extract app_id and calculate app_address
        elif cls is SendAppCreateTransactionResult:
            app_id = result.confirmations[index]["application-index"]  # type: ignore[index]
            base_params.update(
                {
                    "app_id": app_id,
                    "app_address": algosdk.logic.get_application_address(app_id),
                    "abi_return": result.returns[index] if result.returns else None,
                    "compiled_approval": None,  # These would need to be passed in separately
                    "compiled_clear": None,  # if needed
                }
            )
        # For regular app transactions, just add abi_return
        elif cls is SendAppTransactionResult:
            base_params["abi_return"] = result.returns[index] if result.returns else None

        return cls(**base_params)


@dataclass(frozen=True, kw_only=True)
class SendSingleAssetCreateTransactionResult(SendSingleTransactionResult):
    asset_id: int


T = TypeVar("T")


@dataclass(frozen=True)
class _SendAppTransactionResult(Generic[T], SendSingleTransactionResult):
    abi_return: T | None = None


@dataclass(frozen=True)
class SendAppTransactionResult(_SendAppTransactionResult[ABIReturn]):
    pass


@dataclass(frozen=True)
class _SendAppUpdateTransactionResult(Generic[T], SendSingleTransactionResult):
    abi_return: T | None = None
    compiled_approval: Any | None = None
    compiled_clear: Any | None = None


@dataclass(frozen=True)
class SendAppUpdateTransactionResult(_SendAppUpdateTransactionResult[ABIReturn]):
    pass


@dataclass(frozen=True)
class _SendAppCreateTransactionResult(Generic[T], SendSingleTransactionResult):
    app_id: int
    app_address: str
    abi_return: T | None = None
    compiled_approval: Any | None = None
    compiled_clear: Any | None = None


@dataclass(frozen=True, kw_only=True)
class SendAppCreateTransactionResult(_SendAppCreateTransactionResult):
    pass
