"""
Vendored + adapted signer utilities that operate on algokit-transact transactions.
"""

import base64
from collections.abc import Sequence
from typing import Callable

from nacl.signing import SigningKey

from algokit_common.constants import EMPTY_SIGNATURE
from algokit_algosdk import encoding
from algokit_algosdk.logicsig import LogicSigAccount
from algokit_algosdk.multisig import Multisig
from algokit_transact import encode_signed_transaction, encode_transaction
from algokit_transact.models.signed_transaction import SignedTransaction
from algokit_transact.models.transaction import Transaction
from algokit_transact.signing.logic_signature import LogicSignature as AlgoKitLogicSignature
from algokit_transact.signing.types import MultisigSignature, MultisigSubsignature

TransactionSigner = Callable[[Sequence[Transaction], Sequence[int]], list[bytes]]


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
    multisig_signature = _build_multisig_signature(msig, {idx: subsig.signature for idx, subsig in enumerate(msig.subsigs)}) if msig else None

    return AlgoKitLogicSignature(
        logic=lsig.logic,
        args=tuple(lsig.args) if lsig.args else None,
        signature=signature,
        multi_signature=multisig_signature,
    )
