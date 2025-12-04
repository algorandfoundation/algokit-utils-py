"""
Vendored + adapted signer utilities that operate on algokit-transact transactions.
"""

import base64
import dataclasses
from collections.abc import Callable, Sequence

from nacl.signing import SigningKey

from algokit_common.constants import (
    EMPTY_SIGNATURE,
    LOGIC_DATA_DOMAIN_SEPARATOR,
    MX_BYTES_DOMAIN_SEPARATOR,
    MULTISIG_PROGRAM_DOMAIN_SEPARATOR,
    PROGRAM_DOMAIN_SEPARATOR,
    TRANSACTION_DOMAIN_SEPARATOR,
)
from algokit_algosdk import encoding
from algokit_algosdk.logicsig import LogicSigAccount
from algokit_algosdk.multisig import Multisig
from algokit_transact import encode_signed_transaction, encode_transaction
from algokit_transact.models.signed_transaction import SignedTransaction
from algokit_transact.models.transaction import Transaction
from algokit_transact.signing.logic_signature import LogicSignature as AlgoKitLogicSignature
from algokit_transact.signing.types import MultisigSignature, MultisigSubsignature

TransactionSigner = Callable[[Sequence[Transaction], Sequence[int]], list[bytes]]
BytesSigner = Callable[[bytes], bytes]
LsigSigner = Callable[[bytes, bytes | None], bytes]
ProgramDataSigner = Callable[[bytes], bytes]
MxBytesSigner = Callable[[bytes], bytes]


@dataclasses.dataclass(frozen=True)
class SignerAccount:
    """
    An account that provides multiple signer interfaces for secretless signing.

    This dataclass wraps a public key and provides all the signer interfaces
    needed for Algorand operations (transactions, LogicSig delegation, etc.)
    without requiring access to private keys.

    Use `make_signer_account()` to create instances from a public key and
    raw bytes signer callback.

    Attributes:
        address: The Algorand address for this account
        public_key: The 32-byte ed25519 public key
        signer: Transaction signer for signing transaction groups
        lsig_signer: Signer for LogicSig program delegation (single-sig and multisig)
        program_data_signer: Signer for LogicSig data (during tx signing)
        bytes_signer: Raw bytes signer (no domain prefix)
        mx_bytes_signer: Signer for arbitrary bytes with MX domain prefix
    """

    address: str
    public_key: bytes
    signer: TransactionSigner
    lsig_signer: LsigSigner
    program_data_signer: ProgramDataSigner
    bytes_signer: BytesSigner
    mx_bytes_signer: MxBytesSigner


def make_signer_account(public_key: bytes, raw_signer: BytesSigner) -> SignerAccount:
    """
    Create a SignerAccount from a public key and raw bytes signer.

    This factory function generates all the specialized signers needed for
    Algorand operations from a single raw bytes signer callback. It enables
    secretless signing through KMS, hardware wallets, or other external
    signing mechanisms.

    The raw_signer is called with different domain-prefixed data depending
    on the operation:
    - Transaction signing: "TX" + encoded transaction bytes
    - LogicSig delegation: "Program" + program bytes
    - LogicSig data signing: "ProgData" + data bytes

    Args:
        public_key: The 32-byte ed25519 public key for the account
        raw_signer: A callable that signs arbitrary bytes and returns
                   the 64-byte ed25519 signature

    Returns:
        A SignerAccount with all signer interfaces configured

    Example:
        ```python
        # Using a KMS signer
        def kms_signer(data: bytes) -> bytes:
            return kms_client.sign(key_id, data)

        account = make_signer_account(public_key_bytes, kms_signer)

        # Use in transactions
        composer.add_payment(
            PaymentParams(
                sender=account.address,
                receiver="...",
                amount=AlgoAmount.from_algo(1),
                signer=account.signer,
            )
        )
        ```
    """
    account_address = encoding.encode_address(public_key)
    assert isinstance(account_address, str)

    def transaction_signer(txn_group: Sequence[Transaction], indexes: Sequence[int]) -> list[bytes]:
        """Sign transactions using the raw signer with TX domain prefix."""
        blobs: list[bytes] = []
        for index in indexes:
            txn = txn_group[index]
            # The raw signer expects domain-prefixed data
            payload = TRANSACTION_DOMAIN_SEPARATOR.encode() + encode_transaction(txn)
            signature = raw_signer(payload)
            auth_address = account_address if txn.sender != account_address else None
            signed = SignedTransaction(
                transaction=txn,
                signature=signature,
                multi_signature=None,
                logic_signature=None,
                auth_address=auth_address,
            )
            blobs.append(encode_signed_transaction(signed))
        return blobs

    def lsig_signer(program: bytes, msig_address: bytes | None = None) -> bytes:
        """Sign a LogicSig program with appropriate domain prefix."""
        if msig_address:
            payload = MULTISIG_PROGRAM_DOMAIN_SEPARATOR.encode() + msig_address + program
        else:
            payload = PROGRAM_DOMAIN_SEPARATOR.encode() + program
        return raw_signer(payload)

    def program_data_signer(data: bytes) -> bytes:
        """Sign LogicSig data with ProgData domain prefix."""
        payload = LOGIC_DATA_DOMAIN_SEPARATOR.encode() + data
        return raw_signer(payload)

    def mx_bytes_signer(data: bytes) -> bytes:
        """Sign arbitrary bytes with MX domain prefix."""
        payload = MX_BYTES_DOMAIN_SEPARATOR.encode() + data
        return raw_signer(payload)

    return SignerAccount(
        address=account_address,
        public_key=public_key,
        signer=transaction_signer,
        lsig_signer=lsig_signer,
        program_data_signer=program_data_signer,
        bytes_signer=raw_signer,
        mx_bytes_signer=mx_bytes_signer,
    )


def make_basic_account_transaction_signer(private_key: str) -> TransactionSigner:
    """
    Create a signer backed by a private key (base64-encoded).
    """
    private_key_bytes = base64.b64decode(private_key)
    signing_key = SigningKey(private_key_bytes[:32])
    public_key = private_key_bytes[32:]
    account_address = encoding.encode_address(public_key)
    assert isinstance(account_address, str)

    def signer(txn_group: Sequence[Transaction], indexes: Sequence[int]) -> list[bytes]:
        blobs: list[bytes] = []
        for index in indexes:
            txn = txn_group[index]
            signature = signing_key.sign(encode_transaction(txn)).signature
            auth_address = account_address if txn.sender != account_address else None
            signed = SignedTransaction(
                transaction=txn,
                signature=signature,
                multi_signature=None,
                logic_signature=None,
                auth_address=auth_address,
            )
            blobs.append(encode_signed_transaction(signed))
        return blobs

    return signer


def make_logic_sig_transaction_signer(lsig_account: LogicSigAccount) -> TransactionSigner:
    """
    Create a signer that applies a LogicSigAccount to each transaction.
    """

    def signer(txn_group: Sequence[Transaction], indexes: Sequence[int]) -> list[bytes]:
        blobs: list[bytes] = []
        for index in indexes:
            txn = txn_group[index]
            logic_sig = _convert_logic_sig(lsig_account)
            auth_address = lsig_account.address()
            auth_addr = auth_address if txn.sender != auth_address else None

            signed = SignedTransaction(
                transaction=txn,
                signature=None,
                multi_signature=None,
                logic_signature=logic_sig,
                auth_address=auth_addr,
            )
            blobs.append(encode_signed_transaction(signed))
        return blobs

    return signer


def make_multisig_transaction_signer(multisig: Multisig, private_keys: Sequence[str]) -> TransactionSigner:
    """
    Create a signer that signs with the provided multisig parameters and private keys.
    """
    signing_entries: list[tuple[int, SigningKey]] = []
    for private_key in private_keys:
        key_bytes = base64.b64decode(private_key)
        signing_key = SigningKey(key_bytes[:32])
        public_key = key_bytes[32:]
        index = _find_subsig_index(multisig, public_key)
        signing_entries.append((index, signing_key))

    msig_address = multisig.address()
    assert isinstance(msig_address, str)

    def signer(txn_group: Sequence[Transaction], indexes: Sequence[int]) -> list[bytes]:
        blobs: list[bytes] = []
        for index in indexes:
            txn = txn_group[index]
            payload = encode_transaction(txn)
            signatures: dict[int, bytes] = {}
            for subsig_index, signing_key in signing_entries:
                signatures[subsig_index] = signing_key.sign(payload).signature

            multisig_signature = _build_multisig_signature(multisig, signatures)

            signed = SignedTransaction(
                transaction=txn,
                signature=None,
                multi_signature=multisig_signature,
                logic_signature=None,
                auth_address=msig_address if txn.sender != msig_address else None,
            )
            blobs.append(encode_signed_transaction(signed))
        return blobs

    return signer


def make_empty_transaction_signer() -> TransactionSigner:
    """
    Create a signer that injects empty signatures (used for simulation).
    """

    def signer(txn_group: Sequence[Transaction], indexes: Sequence[int]) -> list[bytes]:
        blobs: list[bytes] = []
        for index in indexes:
            txn = txn_group[index]
            signed = SignedTransaction(
                transaction=txn,
                signature=EMPTY_SIGNATURE,
                multi_signature=None,
                logic_signature=None,
                auth_address=None,
            )
            blobs.append(encode_signed_transaction(signed))
        return blobs

    return signer


def _find_subsig_index(multisig: Multisig, public_key: bytes) -> int:
    for idx, subsig in enumerate(multisig.subsigs):
        if subsig.public_key == public_key:
            return idx
    raise ValueError("Private key does not belong to multisig account")


def _build_multisig_signature(multisig: Multisig, sigs: dict[int, bytes]) -> MultisigSignature:
    subsignatures: list[MultisigSubsignature] = []
    for idx, subsig in enumerate(multisig.subsigs):
        addr = encoding.encode_address(subsig.public_key)
        assert isinstance(addr, str)
        subsignatures.append(
            MultisigSubsignature(
                address=addr,
                signature=sigs.get(idx),
            )
        )
    return MultisigSignature(
        version=multisig.version,
        threshold=multisig.threshold,
        subsignatures=tuple(subsignatures),
    )


def _convert_logic_sig(lsig_account: LogicSigAccount) -> AlgoKitLogicSignature:
    lsig = lsig_account.lsig
    signature = base64.b64decode(lsig.sig) if lsig.sig else None
    msig = lsig.msig or lsig.lmsig
    multisig_signature = (
        _build_multisig_signature(msig, {idx: subsig.signature for idx, subsig in enumerate(msig.subsigs)})
        if msig
        else None
    )

    return AlgoKitLogicSignature(
        logic=lsig.logic,
        args=tuple(lsig.args) if lsig.args else None,
        signature=signature,
        multi_signature=multisig_signature,
    )
