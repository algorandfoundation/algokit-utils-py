from typing import Any, Literal, TypedDict, TypeVar, cast

import algosdk


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
