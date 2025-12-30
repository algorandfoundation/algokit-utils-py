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

    def __post_init__(self) -> None:
        if not self.sub_signers:
            raise ValueError("sub_signers cannot be empty")

    @staticmethod
    def from_signature(msig: MultisigSignature) -> "MultisigAccount":
        raise NotImplementedError

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
