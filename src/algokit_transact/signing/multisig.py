from collections.abc import Iterable
from dataclasses import replace

from algokit_common import (
    PUBLIC_KEY_BYTE_LENGTH,
    address_from_public_key,
    public_key_from_address,
    sha512_256,
)
from algokit_transact.signing.types import MultisigSignature, MultisigSubsignature

_MULTISIG_DOMAIN_SEPARATOR = b"MultisigAddr"


def new_multisig_signature(version: int, threshold: int, participants: Iterable[str]) -> MultisigSignature:
    participants = list(participants)
    if version == 0:
        raise ValueError("Version cannot be zero")
    if not participants:
        raise ValueError("Participants cannot be empty")
    if threshold < 1 or threshold > len(participants):
        raise ValueError("Threshold must be greater than zero and less than or equal to the number of participants")

    subsigs = [MultisigSubsignature(public_key=public_key_from_address(address)) for address in participants]
    return MultisigSignature(version=version, threshold=threshold, subsigs=subsigs)


def participants_from_multisig_signature(multisig_signature: MultisigSignature) -> list[str]:
    return [address_from_public_key(subsig.public_key) for subsig in multisig_signature.subsigs]


def address_from_multisig_signature(multisig_signature: MultisigSignature) -> str:
    participant_keys = [subsig.public_key for subsig in multisig_signature.subsigs]

    buffer = bytearray()
    buffer.extend(_MULTISIG_DOMAIN_SEPARATOR)
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
    participant_pk = public_key_from_address(participant)
    for subsig in multisig_signature.subsigs:
        if subsig.public_key == participant_pk:
            found = True
            updated.append(MultisigSubsignature(public_key=subsig.public_key, sig=signature))
        else:
            updated.append(subsig)
    if not found:
        raise ValueError("Address not found in multisig signature")
    return replace(multisig_signature, subsigs=updated)


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
    for subsig_a, subsig_b in zip(multisig_a.subsigs, multisig_b.subsigs, strict=False):
        sig = subsig_b.sig if subsig_b.sig is not None else subsig_a.sig
        merged_subsigs.append(MultisigSubsignature(public_key=subsig_a.public_key, sig=sig))
    return MultisigSignature(
        version=multisig_a.version,
        threshold=multisig_a.threshold,
        subsigs=merged_subsigs,
    )
