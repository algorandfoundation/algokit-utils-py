from typing import Any, Literal, TypedDict, TypeVar

import algosdk

__all__ = [
    "Arc2TransactionNote",
    "BaseArc2Note",
    "JsonFormatArc2Note",
    "SendParams",
    "StringFormatArc2Note",
    "TransactionNote",
    "TransactionNoteData",
    "TransactionWrapper",
]


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

TxnTypeT = TypeVar("TxnTypeT", bound=algosdk.transaction.Transaction)


class TransactionWrapper:
    """Wrapper around algosdk.transaction.Transaction with optional property validators"""

    def __init__(self, transaction: algosdk.transaction.Transaction) -> None:
        self._raw = transaction

    @property
    def raw(self) -> algosdk.transaction.Transaction:
        return self._raw

    @property
    def payment(self) -> algosdk.transaction.PaymentTxn:
        return self._return_if_type(
            algosdk.transaction.PaymentTxn,
        )

    @property
    def keyreg(self) -> algosdk.transaction.KeyregTxn:
        return self._return_if_type(algosdk.transaction.KeyregTxn)

    @property
    def asset_config(self) -> algosdk.transaction.AssetConfigTxn:
        return self._return_if_type(algosdk.transaction.AssetConfigTxn)

    @property
    def asset_transfer(self) -> algosdk.transaction.AssetTransferTxn:
        return self._return_if_type(algosdk.transaction.AssetTransferTxn)

    @property
    def asset_freeze(self) -> algosdk.transaction.AssetFreezeTxn:
        return self._return_if_type(algosdk.transaction.AssetFreezeTxn)

    @property
    def application_call(self) -> algosdk.transaction.ApplicationCallTxn:
        return self._return_if_type(algosdk.transaction.ApplicationCallTxn)

    @property
    def state_proof(self) -> algosdk.transaction.StateProofTxn:
        return self._return_if_type(algosdk.transaction.StateProofTxn)

    def _return_if_type(self, txn_type: type[TxnTypeT]) -> TxnTypeT:
        if isinstance(self._raw, txn_type):
            return self._raw
        raise ValueError(f"Transaction is not of type {txn_type.__name__}")


class SendParams(TypedDict, total=False):
    """Parameters for sending a transaction"""

    max_rounds_to_wait: int | None
    suppress_log: bool | None
    populate_app_call_resources: bool | None
    cover_app_call_inner_transaction_fees: bool | None
