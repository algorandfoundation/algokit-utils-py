import dataclasses
from collections.abc import Sequence
from functools import cached_property
from typing import TYPE_CHECKING

from algokit_common import address_from_public_key
from algokit_transact.codec.signed import encode_signed_transaction
from algokit_transact.codec.transaction import encode_transaction
from algokit_transact.models.signed_transaction import SignedTransaction
from algokit_transact.models.transaction import Transaction as AlgokitTransaction
from algokit_transact.ops.validate import validate_signed_transaction
from algokit_transact.signer import AddressWithSigners
from algokit_transact.signing.multisig import (
    address_from_multisig_signature,
    apply_multisig_subsignature,
    new_multisig_signature,
)
from algokit_transact.signing.types import MultisigSignature

if TYPE_CHECKING:
    from algokit_transact.signer import (
        DelegatedLsigSigner,
        TransactionSigner,
    )
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

    @staticmethod
    def from_signature(msig: MultisigSignature) -> "MultisigAccount":
        """
        Create a MultisigAccount from a MultisigSignature.

        This is primarily used to extract the multisig address from a signature,
        such as when dealing with delegated logic signatures.

        Args:
            msig: The multisig signature to create the account from

        Returns:
            A MultisigAccount with no sub-signers
        """
        params = MultisigMetadata(
            version=msig.version,
            threshold=msig.threshold,
            addrs=[address_from_public_key(subsig.public_key) for subsig in msig.subsigs],
        )
        return MultisigAccount(params=params, sub_signers=[])

    @cached_property
    def _multisig_signature(self) -> MultisigSignature:
        return new_multisig_signature(
            self.params.version,
            self.params.threshold,
            self.params.addrs,
        )

    @cached_property
    def signer(self) -> "TransactionSigner":
        address_to_signer = {account.addr: account.bytes_signer for account in self.sub_signers}
        msig_address = self.address
        base_multisig = self._multisig_signature

        def signer(txn_group: Sequence[AlgokitTransaction], indexes_to_sign: Sequence[int]) -> list[bytes]:
            blobs: list[bytes] = []
            for index in indexes_to_sign:
                txn = txn_group[index]
                payload = encode_transaction(txn)

                multisig_sig = base_multisig
                for subsig in base_multisig.subsigs:
                    subsig_addr = address_from_public_key(subsig.public_key)
                    if subsig_addr in address_to_signer:
                        signature = address_to_signer[subsig_addr](payload)
                        multisig_sig = apply_multisig_subsignature(multisig_sig, subsig_addr, signature)

                signed = SignedTransaction(
                    txn=txn,
                    sig=None,
                    msig=multisig_sig,
                    lsig=None,
                    auth_address=msig_address if txn.sender != msig_address else None,
                )
                validate_signed_transaction(signed)
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

    @cached_property
    def delegated_lsig_signer(self) -> "DelegatedLsigSigner":
        from algokit_transact.logicsig import DelegatedLsigResult, LogicSigAccount

        def delegated_signer(lsig: LogicSigAccount, _: MultisigAccount | None) -> DelegatedLsigResult:
            lmsig = lsig.lmsig or self._multisig_signature

            for addr_with_signer in self.sub_signers:
                addr = addr_with_signer.addr
                result = addr_with_signer.delegated_lsig_signer(lsig, self)
                if result.sig is None:
                    raise ValueError(
                        f"Signer for address {addr} did not produce a valid signature when signing logic sig"
                        f" for multisig account {self.addr}",
                    )

                lmsig = self.apply_signature(lmsig, addr, result.sig)

            return DelegatedLsigResult(addr=self.addr, lmsig=lmsig)

        return delegated_signer

    def apply_signature(self, msig: MultisigSignature, address: str, sig: bytes) -> MultisigSignature:
        expected = self.params
        if msig.version != expected.version or msig.threshold != expected.threshold:
            given = MultisigMetadata(
                version=msig.version,
                threshold=msig.threshold,
                addrs=[address_from_public_key(s.public_key) for s in msig.subsigs],
            )

            raise ValueError(
                f"Multisig signature parameters do not match expected multisig parameters. {expected=!r}, {given=!r}"
            )
        return apply_multisig_subsignature(msig, address, sig)

    def create_multisig_transaction(self, txn: AlgokitTransaction) -> SignedTransaction:
        """
        Create a multisig transaction without any signatures.

        Args:
            txn: The transaction to create a multisig transaction for

        Returns:
            A SignedTransaction with empty multisig structure
        """
        msig = self.create_multisig_signature()

        auth_address = self.address if txn.sender != self.address else None

        return SignedTransaction(
            txn=txn,
            sig=None,
            msig=msig,
            lsig=None,
            auth_address=auth_address,
        )

    def create_multisig_signature(self) -> MultisigSignature:
        """
        Create an empty multisig signature structure.

        Returns:
            A MultisigSignature with empty signatures
        """
        return new_multisig_signature(
            self.params.version,
            self.params.threshold,
            self.params.addrs,
        )

    def apply_signature_to_txn(self, txn: SignedTransaction, pubkey: bytes, signature: bytes) -> SignedTransaction:
        """
        Apply a signature to a signed transaction, returning a new SignedTransaction.

        Note: Unlike TypeScript which mutates in place, this returns a new SignedTransaction
        since Python's SignedTransaction is a frozen dataclass.

        Args:
            txn: The signed transaction to apply the signature to
            pubkey: The public key of the signer
            signature: The signature to apply

        Returns:
            A new SignedTransaction with the signature applied
        """
        from dataclasses import replace

        msig = txn.msig
        if not msig:
            created_txn = self.create_multisig_transaction(txn.txn)
            msig = created_txn.msig

        if not msig:
            raise ValueError("Failed to create multisig signature")

        # Convert to address for validation via apply_signature
        address = address_from_public_key(pubkey)
        updated_msig = self.apply_signature(msig, address, signature)

        return replace(txn, msig=updated_msig)
