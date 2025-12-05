"""Transaction and data signing types and utilities."""

import base64
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

import nacl.signing

from algokit_common import address_from_public_key, public_key_from_address
from algokit_common.constants import (
    EMPTY_SIGNATURE,
    LOGIC_DATA_DOMAIN_SEPARATOR,
    MULTISIG_PROGRAM_DOMAIN_SEPARATOR,
    MX_BYTES_DOMAIN_SEPARATOR,
    PROGRAM_DOMAIN_SEPARATOR,
)
from algokit_transact.codec.signed import encode_signed_transaction
from algokit_transact.codec.transaction import encode_transaction
from algokit_transact.models.signed_transaction import SignedTransaction
from algokit_transact.models.transaction import Transaction

# Type aliases for signing functions
BytesSigner = Callable[[bytes], bytes]
TransactionSigner = Callable[[Sequence[Transaction], Sequence[int]], list[bytes]]
LsigSigner = Callable[[bytes, bytes | None], bytes]
ProgramDataSigner = Callable[[bytes, bytes], bytes]
MxBytesSigner = Callable[[bytes], bytes]


@runtime_checkable
class HasAddress(Protocol):
    """Protocol for objects with an address."""

    @property
    def addr(self) -> str: ...


@runtime_checkable
class HasTransactionSigner(HasAddress, Protocol):
    """Protocol for objects with transaction signing capability."""

    @property
    def signer(self) -> TransactionSigner: ...


@runtime_checkable
class HasLsigSigner(HasAddress, Protocol):
    """Protocol for objects with logic signature delegation signing."""

    @property
    def lsig_signer(self) -> LsigSigner: ...


@runtime_checkable
class HasProgramDataSigner(HasAddress, Protocol):
    """Protocol for objects with program data signing capability."""

    @property
    def program_data_signer(self) -> ProgramDataSigner: ...


@runtime_checkable
class HasMxBytesSigner(HasAddress, Protocol):
    """Protocol for objects with MX-prefixed bytes signing capability."""

    @property
    def mx_bytes_signer(self) -> MxBytesSigner: ...


SendingAddress = str | HasTransactionSigner


@dataclass(frozen=True, slots=True)
class AddressWithSigners:
    """Container for an address with all signing capabilities."""

    addr: str
    signer: TransactionSigner
    lsig_signer: LsigSigner
    program_data_signer: ProgramDataSigner
    bytes_signer: BytesSigner
    mx_bytes_signer: MxBytesSigner


def generate_address_with_signers(
    ed25519_pubkey: bytes,
    raw_ed25519_signer: BytesSigner,
) -> AddressWithSigners:
    """Generate domain-separated signers from an ed25519 pubkey and raw signer."""
    addr = address_from_public_key(ed25519_pubkey)

    def transaction_signer(txn_group: Sequence[Transaction], indexes_to_sign: Sequence[int]) -> list[bytes]:
        result: list[bytes] = []
        for index in indexes_to_sign:
            txn = txn_group[index]
            bytes_to_sign = encode_transaction(txn)
            signature = raw_ed25519_signer(bytes_to_sign)
            stxn = SignedTransaction(
                transaction=txn,
                signature=signature,
                auth_address=addr if txn.sender != addr else None,
            )
            result.append(encode_signed_transaction(stxn))
        return result

    def lsig_signer(program: bytes, msig_address: bytes | None = None) -> bytes:
        if msig_address is not None:
            payload = MULTISIG_PROGRAM_DOMAIN_SEPARATOR.encode() + msig_address + program
        else:
            payload = PROGRAM_DOMAIN_SEPARATOR.encode() + program
        return raw_ed25519_signer(payload)

    def program_data_signer(data: bytes, program_address: bytes) -> bytes:
        payload = LOGIC_DATA_DOMAIN_SEPARATOR.encode() + program_address + data
        return raw_ed25519_signer(payload)

    def mx_bytes_signer(data: bytes) -> bytes:
        payload = MX_BYTES_DOMAIN_SEPARATOR.encode() + data
        return raw_ed25519_signer(payload)

    return AddressWithSigners(
        addr=addr,
        signer=transaction_signer,
        lsig_signer=lsig_signer,
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
                transaction=txn_group[index],
                signature=EMPTY_SIGNATURE,
            )
            result.append(encode_signed_transaction(stxn))
        return result

    return empty_signer


def bytes_to_sign_for_delegation(program: bytes, msig_public_key: bytes | None = None) -> bytes:
    """Get bytes to sign for delegating a logic signature."""
    if msig_public_key is not None:
        return MULTISIG_PROGRAM_DOMAIN_SEPARATOR.encode() + msig_public_key + program
    return PROGRAM_DOMAIN_SEPARATOR.encode() + program


def program_data_to_sign(data: bytes, program_address: str) -> bytes:
    """Get bytes to sign for program data."""
    program_public_key = public_key_from_address(program_address)
    return LOGIC_DATA_DOMAIN_SEPARATOR.encode() + program_public_key + data


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
