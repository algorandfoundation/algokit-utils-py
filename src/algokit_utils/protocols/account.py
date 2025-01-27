from typing import Protocol, runtime_checkable

from algosdk.atomic_transaction_composer import TransactionSigner

__all__ = ["TransactionSignerAccountProtocol"]


@runtime_checkable
class TransactionSignerAccountProtocol(Protocol):
    """An account that has a transaction signer.
    Implemented by SigningAccount, LogicSigAccount, MultiSigAccount and TransactionSignerAccount abstractions.
    """

    @property
    def address(self) -> str:
        """The address of the account."""
        ...

    @property
    def signer(self) -> TransactionSigner:
        """The transaction signer for the account."""
        ...
