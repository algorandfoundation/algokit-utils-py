from typing import Protocol, runtime_checkable

from algokit_utils.protocols.signer import TransactionSigner

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
        """The AlgoKit-native signer callable."""
        ...
