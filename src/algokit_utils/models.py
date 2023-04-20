import dataclasses
from collections.abc import Sequence
from typing import Any, Protocol, TypeAlias, TypedDict

from algosdk import transaction
from algosdk.abi import Method
from algosdk.atomic_transaction_composer import AtomicTransactionResponse, TransactionSigner


@dataclasses.dataclass(kw_only=True)
class Account:
    """Holds the private_key and address for an account"""

    private_key: str
    address: str


@dataclasses.dataclass(kw_only=True)
class TransactionResponse:
    """Response for a non ABI call"""

    tx_id: str
    """Transaction Id"""
    confirmed_round: int | None
    """Round transaction was confirmed, `None` if call was a from a dry-run"""

    @staticmethod
    def from_atr(result: AtomicTransactionResponse, transaction_index: int = 0) -> "TransactionResponse":
        tx_id = result.tx_ids[transaction_index]
        abi_result = next((r for r in result.abi_results if r.tx_id == tx_id), None)
        if abi_result:
            return ABITransactionResponse(
                tx_id=tx_id,
                raw_value=abi_result.raw_value,
                return_value=abi_result.return_value,
                decode_error=abi_result.decode_error,
                tx_info=abi_result.tx_info,
                method=abi_result.method,
                confirmed_round=result.confirmed_round,
            )
        else:
            return TransactionResponse(
                tx_id=tx_id,
                confirmed_round=result.confirmed_round,
            )


@dataclasses.dataclass(kw_only=True)
class ABITransactionResponse(TransactionResponse):
    """Response for an ABI call"""

    raw_value: bytes
    """The raw response before ABI decoding"""
    return_value: Any
    """Decoded ABI result"""
    decode_error: Exception | None
    """Details of error that occurred when attempting to decode raw_value"""
    tx_info: dict
    """Details of transaction"""
    method: Method
    """ABI method used to make call"""


ABIArgType = Any
ABIArgsDict = dict[str, ABIArgType]


class ABIReturnSubroutine(Protocol):
    def method_spec(self) -> Method:
        ...


ABIMethod: TypeAlias = ABIReturnSubroutine | Method | str


@dataclasses.dataclass(kw_only=True)
class CommonCallParameters:
    """Common transaction parameters used when making update, delete, opt_in, close_out or clear_state calls"""

    signer: TransactionSigner | None = None
    sender: str | None = None
    suggested_params: transaction.SuggestedParams | None = None
    note: bytes | str | None = None
    lease: bytes | str | None = None
    accounts: list[str] | None = None
    foreign_apps: list[int] | None = None
    foreign_assets: list[int] | None = None
    boxes: Sequence[tuple[int, bytes | bytearray | str | int]] | None = None
    rekey_to: str | None = None


@dataclasses.dataclass(kw_only=True)
class OnCompleteCallParameters(CommonCallParameters):
    """Transaction parameters used when making any call to an Application"""

    on_complete: transaction.OnComplete | None = None


@dataclasses.dataclass(kw_only=True)
class CreateCallParameters(OnCompleteCallParameters):
    """Transaction parameters used when making a create call for Application"""

    extra_pages: int | None = None


class CommonCallParametersDict(TypedDict, total=False):
    """Common transaction parameters used when making update, delete, opt_in, close_out or clear_state calls"""

    signer: TransactionSigner
    sender: str
    suggested_params: transaction.SuggestedParams
    note: bytes | str
    lease: bytes | str


class OnCompleteCallParametersDict(TypedDict, CommonCallParametersDict, total=False):
    """Transaction parameters used when making any call to an Application"""

    on_complete: transaction.OnComplete


class CreateCallParametersDict(TypedDict, OnCompleteCallParametersDict, total=False):
    """Transaction parameters used when making a create call for Application"""

    extra_pages: int
