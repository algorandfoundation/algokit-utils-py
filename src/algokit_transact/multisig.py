from __future__ import annotations

import dataclasses
from collections.abc import Callable, Sequence

from algokit_transact.codec.signed import encode_signed_transaction
from algokit_transact.codec.transaction import encode_transaction
from algokit_transact.models.signed_transaction import SignedTransaction
from algokit_transact.models.transaction import Transaction as AlgokitTransaction
from algokit_transact.signer import AddressWithSigners, TransactionSigner
from algokit_transact.signing.multisig import (
    address_from_multisig_signature,
    apply_multisig_subsignature,
    new_multisig_signature,
)
from algokit_transact.signing.types import MultisigSignature

__all__ = [
    "MultisigAccount",
    "MultisigMetadata",
]


@dataclasses.dataclass(kw_only=True)
class MultisigMetadata:
    """Metadata for a multisig account."""

    version: int
    threshold: int
    addrs: list[str]


@dataclasses.dataclass(kw_only=True)
class MultisigAccount:
    """Account wrapper for multisig signing. Supports secretless signing."""

    _params: MultisigMetadata
    _sub_signers: Sequence[AddressWithSigners]
    _addr: str
    _signer: TransactionSigner
    _multisig_signature: MultisigSignature

    def __init__(
        self,
        multisig_params: MultisigMetadata,
        sub_signers: Sequence[AddressWithSigners],
    ) -> None:
        self._params = multisig_params
        self._sub_signers = sub_signers
        self._multisig_signature = new_multisig_signature(
            multisig_params.version,
            multisig_params.threshold,
            multisig_params.addrs,
        )
        self._addr = address_from_multisig_signature(self._multisig_signature)
        self._signer = self._create_multisig_signer()

    def _get_account_address(self, account: AddressWithSigners) -> str:
        """Get address from account, handling both AddressWithSigners and AddressWithSigners."""
        return account.addr

    def _create_multisig_signer(self) -> TransactionSigner:
        address_to_signer: dict[str, Callable[[bytes], bytes]] = {
            self._get_account_address(account): account.bytes_signer for account in self._sub_signers
        }
        msig_address = self._addr
        base_multisig = self._multisig_signature

        def signer(txn_group: Sequence[AlgokitTransaction], indexes_to_sign: Sequence[int]) -> list[bytes]:
            blobs: list[bytes] = []
            for index in indexes_to_sign:
                txn = txn_group[index]
                payload = encode_transaction(txn)

                multisig_sig = base_multisig
                for subsig in base_multisig.subsignatures:
                    if subsig.address in address_to_signer:
                        signature = address_to_signer[subsig.address](payload)
                        multisig_sig = apply_multisig_subsignature(multisig_sig, subsig.address, signature)

                signed = SignedTransaction(
                    transaction=txn,
                    signature=None,
                    multi_signature=multisig_sig,
                    logic_signature=None,
                    auth_address=msig_address if txn.sender != msig_address else None,
                )
                blobs.append(encode_signed_transaction(signed))
            return blobs

        return signer

    @property
    def params(self) -> MultisigMetadata:
        """The multisig account parameters."""
        return self._params

    @property
    def sub_signers(self) -> Sequence[AddressWithSigners]:
        """The list of signing accounts."""
        return self._sub_signers

    @property
    def address(self) -> str:
        """The multisig account address."""
        return self._addr

    @property
    def addr(self) -> str:
        """Alias for address property (matching TypeScript's get addr())."""
        return self.address

    @property
    def signer(self) -> TransactionSigner:
        """Transaction signer callable."""
        return self._signer
