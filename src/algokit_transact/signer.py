"""Transaction and data signing types and utilities."""

import base64
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol, runtime_checkable

import nacl.signing

from algokit_common import address_from_public_key
from algokit_common.constants import EMPTY_SIGNATURE
from algokit_transact.codec.signed import encode_signed_transaction
from algokit_transact.codec.transaction import encode_transaction
from algokit_transact.models.signed_transaction import SignedTransaction
from algokit_transact.models.transaction import Transaction
from algokit_transact.ops.validate import validate_signed_transaction

if TYPE_CHECKING:
    from algokit_transact.logicsig import (
        DelegatedLsigResult,
        LogicSig,
        LogicSigAccount,
    )
    from algokit_transact.multisig import MultisigAccount
_MX_BYTES_DOMAIN_SEPARATOR = b"MX"

DelegatedLsigSigner = Callable[["LogicSigAccount", "MultisigAccount | None"], "DelegatedLsigResult"]
ProgramDataSigner = Callable[["LogicSig", bytes], bytes]
TransactionSigner = Callable[["Sequence[Transaction]", Sequence[int]], list[bytes]]
BytesSigner = Callable[[bytes], bytes]
MxBytesSigner = Callable[[bytes], bytes]


@runtime_checkable
class Addressable(Protocol):
    """Protocol for objects with an address."""

    @property
    def addr(self) -> str: ...


@runtime_checkable
class AddressWithTransactionSigner(Addressable, Protocol):
    """Protocol for objects with transaction signing capability."""

    @property
    def signer(self) -> TransactionSigner: ...


@runtime_checkable
class AddressWithDelegatedLsigSigner(Addressable, Protocol):
    """Protocol for objects with logic signature delegation signing."""

    @property
    def delegated_lsig_signer(self) -> DelegatedLsigSigner: ...


@runtime_checkable
class AddressWithProgramDataSigner(Addressable, Protocol):
    """Protocol for objects with program data signing capability."""

    @property
    def program_data_signer(self) -> ProgramDataSigner: ...


@runtime_checkable
class AddressWithMxBytesSigner(Addressable, Protocol):
    """Protocol for objects with MX-prefixed bytes signing capability."""

    @property
    def mx_bytes_signer(self) -> MxBytesSigner: ...


@dataclass(frozen=True, slots=True)
class AddressWithSigners:
    """Container for an address with all signing capabilities."""

    addr: str
    signer: TransactionSigner
    delegated_lsig_signer: DelegatedLsigSigner
    program_data_signer: ProgramDataSigner
    bytes_signer: BytesSigner
    mx_bytes_signer: MxBytesSigner


def generate_address_with_signers(
    ed25519_pubkey: bytes,
    raw_ed25519_signer: BytesSigner,
    *,
    sending_address: str | None = None,
) -> AddressWithSigners:
    """Generate domain-separated signers from an ed25519 pubkey and raw signer.

    Args:
        ed25519_pubkey: The ed25519 public key bytes.
        raw_ed25519_signer: A function that signs raw bytes with the ed25519 private key.
        sending_address: Optional address to use as the sending address. If provided,
            this will be the `addr` in the returned object, and the address derived
            from `ed25519_pubkey` will be used as the auth_address when signing
            transactions where the sender differs from the sending_address.

    Returns:
        An AddressWithSigners containing the address and all signing functions.
    """
    auth_addr = address_from_public_key(ed25519_pubkey)
    addr = sending_address if sending_address is not None else auth_addr

    def transaction_signer(txn_group: Sequence[Transaction], indexes_to_sign: Sequence[int]) -> list[bytes]:
        result: list[bytes] = []
        for index in indexes_to_sign:
            txn = txn_group[index]
            bytes_to_sign = encode_transaction(txn)
            signature = raw_ed25519_signer(bytes_to_sign)
            stxn = SignedTransaction(
                txn=txn,
                sig=signature,
                auth_address=auth_addr if txn.sender != auth_addr else None,
            )
            validate_signed_transaction(stxn)
            result.append(encode_signed_transaction(stxn))
        return result

    def delegated_lsig_signer(lsig: "LogicSigAccount", msig: "MultisigAccount | None" = None) -> "DelegatedLsigResult":
        from algokit_transact import DelegatedLsigResult

        payload = lsig.bytes_to_sign_for_delegation(msig.address if msig else None)
        sig = raw_ed25519_signer(payload)
        return DelegatedLsigResult(addr=addr, sig=sig)

    def program_data_signer(lsig: "LogicSig", data: bytes) -> bytes:
        payload = lsig.program_data_to_sign(data)
        return raw_ed25519_signer(payload)

    def mx_bytes_signer(data: bytes) -> bytes:
        payload = _MX_BYTES_DOMAIN_SEPARATOR + data
        return raw_ed25519_signer(payload)

    return AddressWithSigners(
        addr=addr,
        signer=transaction_signer,
        delegated_lsig_signer=delegated_lsig_signer,
        program_data_signer=program_data_signer,
        bytes_signer=raw_ed25519_signer,
        mx_bytes_signer=mx_bytes_signer,
    )


def make_empty_transaction_signer() -> TransactionSigner:
    """Create a signer that returns empty signatures (for simulation only)."""

    def empty_signer(txn_group: Sequence[Transaction], indexes_to_sign: Sequence[int]) -> list[bytes]:
        result: list[bytes] = []
        for index in indexes_to_sign:
            stxn = SignedTransaction(
                txn=txn_group[index],
                sig=EMPTY_SIGNATURE,
            )
            validate_signed_transaction(stxn)
            result.append(encode_signed_transaction(stxn))
        return result

    return empty_signer


def make_basic_account_transaction_signer(private_key: str) -> TransactionSigner:
    """Create a transaction signer from a base64-encoded private key.

    Args:
        private_key: Base64-encoded 64-byte private key (first 32 bytes are seed,
            last 32 bytes are public key).

    Returns:
        A TransactionSigner function that can sign transactions.
    """
    # Decode the base64 private key (64 bytes: 32-byte seed + 32-byte public key)
    key_bytes = base64.b64decode(private_key)
    seed = key_bytes[:32]
    public_key = key_bytes[32:]

    # Create signing key from seed
    signing_key = nacl.signing.SigningKey(seed)

    def raw_signer(bytes_to_sign: bytes) -> bytes:
        signed = signing_key.sign(bytes_to_sign)
        return signed.signature

    return generate_address_with_signers(public_key, raw_signer).signer
