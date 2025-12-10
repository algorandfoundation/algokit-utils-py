from __future__ import annotations

import dataclasses
from collections.abc import Callable, Sequence
from functools import cached_property

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


@dataclasses.dataclass(frozen=True)
class MultisigAccount:
    """Account wrapper for multisig signing. Supports secretless signing."""

    params: MultisigMetadata
    """The multisig account parameters."""
    sub_signers: Sequence[AddressWithSigners]
    """The list of signing accounts."""

    @cached_property
    def _multisig_signature(self) -> MultisigSignature:
        return new_multisig_signature(
            self.params.version,
            self.params.threshold,
            self.params.addrs,
        )

    @cached_property
    def signer(self) -> TransactionSigner:
        address_to_signer: dict[str, Callable[[bytes], bytes]] = {
            account.addr: account.bytes_signer for account in self.sub_signers
        }
        msig_address = self.address
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

    @cached_property
    def address(self) -> str:
        """The multisig account address."""
        return address_from_multisig_signature(self._multisig_signature)

    @property
    def addr(self) -> str:
        """Alias for address property (matching TypeScript's get addr())."""
        return self.address
