from __future__ import annotations

from collections.abc import Iterable
from dataclasses import replace

from .address import address_from_public_key, public_key_from_address
from .constants import MULTISIG_DOMAIN_SEPARATOR, PUBLIC_KEY_BYTE_LENGTH
from .hashing import sha512_256
from .types import MultisigSignature, MultisigSubsignature


def new_multisig_signature(version: int, threshold: int, participants: Iterable[str]) -> MultisigSignature:
    participants = tuple(participants)
    if version == 0:
        raise ValueError("Version cannot be zero")
    if not participants:
        raise ValueError("Participants cannot be empty")
    if threshold == 0 or threshold > len(participants):
        raise ValueError("Threshold must be greater than zero and less than or equal to the number of participants")

    subsignatures = tuple(MultisigSubsignature(address=address) for address in participants)
    return MultisigSignature(version=version, threshold=threshold, subsignatures=subsignatures)


def participants_from_multisig_signature(multisig_signature: MultisigSignature) -> tuple[str, ...]:
    return tuple(subsig.address for subsig in multisig_signature.subsignatures)


def address_from_multisig_signature(multisig_signature: MultisigSignature) -> str:
    prefix = MULTISIG_DOMAIN_SEPARATOR.encode()
    participant_keys = [public_key_from_address(subsig.address) for subsig in multisig_signature.subsignatures]

    buffer = bytearray()
    buffer.extend(prefix)
    buffer.append(multisig_signature.version)
    buffer.append(multisig_signature.threshold)
    for pk in participant_keys:
        if len(pk) != PUBLIC_KEY_BYTE_LENGTH:
            raise ValueError("Invalid participant public key length")
        buffer.extend(pk)

    public_key = sha512_256(bytes(buffer))
    return address_from_public_key(public_key)


def apply_multisig_subsignature(
    multisig_signature: MultisigSignature, participant: str, signature: bytes
) -> MultisigSignature:
    found = False
    updated = []
    for subsig in multisig_signature.subsignatures:
        if subsig.address == participant:
            found = True
            updated.append(MultisigSubsignature(address=subsig.address, signature=signature))
        else:
            updated.append(subsig)
    if not found:
        raise ValueError("Address not found in multisig signature")
    return replace(multisig_signature, subsignatures=tuple(updated))


def merge_multisignatures(multisig_a: MultisigSignature, multisig_b: MultisigSignature) -> MultisigSignature:
    if multisig_a.version != multisig_b.version:
        raise ValueError("Cannot merge multisig signatures with different versions")
    if multisig_a.threshold != multisig_b.threshold:
        raise ValueError("Cannot merge multisig signatures with different thresholds")

    participants_a = participants_from_multisig_signature(multisig_a)
    participants_b = participants_from_multisig_signature(multisig_b)
    if participants_a != participants_b:
        raise ValueError("Cannot merge multisig signatures with different participants")

    merged_subsigs = []
    for subsig_a, subsig_b in zip(multisig_a.subsignatures, multisig_b.subsignatures, strict=False):
        signature = subsig_b.signature if subsig_b.signature is not None else subsig_a.signature
        merged_subsigs.append(MultisigSubsignature(address=subsig_a.address, signature=signature))
    return MultisigSignature(
        version=multisig_a.version,
        threshold=multisig_a.threshold,
        subsignatures=tuple(merged_subsigs),
    )
