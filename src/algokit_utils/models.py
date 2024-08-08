import dataclasses
from collections.abc import Sequence
from typing import Any, Generic, Protocol, TypeAlias, TypedDict, TypeVar

import algosdk.account
from algosdk import transaction
from algosdk.abi import Method
from algosdk.atomic_transaction_composer import (
    AccountTransactionSigner,
    AtomicTransactionResponse,
    SimulateAtomicTransactionResponse,
    TransactionSigner,
)
from algosdk.encoding import decode_address
from deprecated import deprecated

__all__ = [
    "ABIArgsDict",
    "ABIMethod",
    "ABITransactionResponse",
    "Account",
    "CreateCallParameters",
    "CreateCallParametersDict",
    "CreateTransactionParameters",
    "OnCompleteCallParameters",
    "OnCompleteCallParametersDict",
    "TransactionParameters",
    "TransactionResponse",
]

ReturnType = TypeVar("ReturnType")


@dataclasses.dataclass(kw_only=True)
class Account:
    """Holds the private_key and address for an account"""

    private_key: str
    """Base64 encoded private key"""
    address: str = dataclasses.field(default="")
    """Address for this account"""

    def __post_init__(self) -> None:
        if not self.address:
            self.address = algosdk.account.address_from_private_key(self.private_key)  # type: ignore[no-untyped-call]

    @property
    def public_key(self) -> bytes:
        """The public key for this account"""
        public_key = decode_address(self.address)  # type: ignore[no-untyped-call]
        assert isinstance(public_key, bytes)
        return public_key

    @property
    def signer(self) -> AccountTransactionSigner:
        """An AccountTransactionSigner for this account"""
        return AccountTransactionSigner(self.private_key)

    @staticmethod
    def new_account() -> "Account":
        private_key, address = algosdk.account.generate_account()  # type: ignore[no-untyped-call]
        return Account(private_key=private_key)


@dataclasses.dataclass(kw_only=True)
class TransactionResponse:
    """Response for a non ABI call"""

    tx_id: str
    """Transaction Id"""
    confirmed_round: int | None
    """Round transaction was confirmed, `None` if call was a from a dry-run"""

    @staticmethod
    def from_atr(
        result: AtomicTransactionResponse | SimulateAtomicTransactionResponse, transaction_index: int = -1
    ) -> "TransactionResponse":
        """Returns either an ABITransactionResponse or a TransactionResponse based on the type of the transaction
        referred to by transaction_index
        :param AtomicTransactionResponse result: Result containing one or more transactions
        :param int transaction_index: Which transaction in the result to return, defaults to -1 (the last transaction)
        """
        tx_id = result.tx_ids[transaction_index]
        abi_result = next((r for r in result.abi_results if r.tx_id == tx_id), None)
        confirmed_round = None if isinstance(result, SimulateAtomicTransactionResponse) else result.confirmed_round
        if abi_result:
            return ABITransactionResponse(
                tx_id=tx_id,
                raw_value=abi_result.raw_value,
                return_value=abi_result.return_value,
                decode_error=abi_result.decode_error,
                tx_info=abi_result.tx_info,
                method=abi_result.method,
                confirmed_round=confirmed_round,
            )
        else:
            return TransactionResponse(
                tx_id=tx_id,
                confirmed_round=confirmed_round,
            )


@dataclasses.dataclass(kw_only=True)
class ABITransactionResponse(TransactionResponse, Generic[ReturnType]):
    """Response for an ABI call"""

    raw_value: bytes
    """The raw response before ABI decoding"""
    return_value: ReturnType
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
    def method_spec(self) -> Method: ...


ABIMethod: TypeAlias = ABIReturnSubroutine | Method | str


@dataclasses.dataclass(kw_only=True)
class TransactionParameters:
    """Additional parameters that can be included in a transaction"""

    signer: TransactionSigner | None = None
    """Signer to use when signing this transaction"""
    sender: str | None = None
    """Sender of this transaction"""
    suggested_params: transaction.SuggestedParams | None = None
    """SuggestedParams to use for this transaction"""
    note: bytes | str | None = None
    """Note for this transaction"""
    lease: bytes | str | None = None
    """Lease value for this transaction"""
    boxes: Sequence[tuple[int, bytes | bytearray | str | int]] | None = None
    """Box references to include in transaction. A sequence of (app id, box key) tuples"""
    accounts: list[str] | None = None
    """Accounts to include in transaction"""
    foreign_apps: list[int] | None = None
    """List of foreign apps (by app id) to include in transaction"""
    foreign_assets: list[int] | None = None
    """List of foreign assets (by asset id) to include in transaction"""
    rekey_to: str | None = None
    """Address to rekey to"""


# CreateTransactionParameters is used by algokit-client-generator clients
@dataclasses.dataclass(kw_only=True)
class CreateTransactionParameters(TransactionParameters):
    """Additional parameters that can be included in a transaction when calling a create method"""

    extra_pages: int | None = None


@dataclasses.dataclass(kw_only=True)
class OnCompleteCallParameters(TransactionParameters):
    """Additional parameters that can be included in a transaction when using the
    ApplicationClient.call/compose_call methods"""

    on_complete: transaction.OnComplete | None = None


@dataclasses.dataclass(kw_only=True)
class CreateCallParameters(OnCompleteCallParameters):
    """Additional parameters that can be included in a transaction when using the
    ApplicationClient.create/compose_create methods"""

    extra_pages: int | None = None


class TransactionParametersDict(TypedDict, total=False):
    """Additional parameters that can be included in a transaction"""

    signer: TransactionSigner
    """Signer to use when signing this transaction"""
    sender: str
    """Sender of this transaction"""
    suggested_params: transaction.SuggestedParams
    """SuggestedParams to use for this transaction"""
    note: bytes | str
    """Note for this transaction"""
    lease: bytes | str
    """Lease value for this transaction"""
    boxes: Sequence[tuple[int, bytes | bytearray | str | int]]
    """Box references to include in transaction. A sequence of (app id, box key) tuples"""
    accounts: list[str]
    """Accounts to include in transaction"""
    foreign_apps: list[int]
    """List of foreign apps (by app id) to include in transaction"""
    foreign_assets: list[int]
    """List of foreign assets (by asset id) to include in transaction"""
    rekey_to: str
    """Address to rekey to"""


class OnCompleteCallParametersDict(TypedDict, TransactionParametersDict, total=False):
    """Additional parameters that can be included in a transaction when using the
    ApplicationClient.call/compose_call methods"""

    on_complete: transaction.OnComplete


class CreateCallParametersDict(TypedDict, OnCompleteCallParametersDict, total=False):
    """Additional parameters that can be included in a transaction when using the
    ApplicationClient.create/compose_create methods"""

    extra_pages: int


# Pre 1.3.1 backwards compatibility
@deprecated(reason="Use TransactionParameters instead", version="1.3.1")
class RawTransactionParameters(TransactionParameters):
    """Deprecated, use TransactionParameters instead"""


@deprecated(reason="Use TransactionParameters instead", version="1.3.1")
class CommonCallParameters(TransactionParameters):
    """Deprecated, use TransactionParameters instead"""


@deprecated(reason="Use TransactionParametersDict instead", version="1.3.1")
class CommonCallParametersDict(TransactionParametersDict):
    """Deprecated, use TransactionParametersDict instead"""


@dataclasses.dataclass
class SimulationTrace:
    app_budget_added: int | None
    app_budget_consumed: int | None
    failure_message: str | None
    exec_trace: dict[str, object]
