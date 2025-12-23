from collections.abc import Mapping
from dataclasses import dataclass, field

from algokit_transact.codec.serde import from_wire, to_wire, wire


def _encode_subsig_seq(value: object) -> object:
    if value is None:
        return None
    if isinstance(value, tuple | list):
        payload = [to_wire(subsig) for subsig in value]
        return payload if payload else None
    return value


def _decode_subsig_seq(value: object) -> object:
    if isinstance(value, list):
        decoded: list[MultisigSubsignature] = []
        for entry in value:
            if isinstance(entry, Mapping):
                decoded.append(from_wire(MultisigSubsignature, entry))
        return tuple(decoded)
    return value


@dataclass(slots=True, frozen=True)
class MultisigSubsignature:
    public_key: bytes = field(metadata=wire("pk"))
    sig: bytes | None = field(default=None, metadata=wire("s"))


@dataclass(slots=True, frozen=True)
class MultisigSignature:
    version: int = field(metadata=wire("v", keep_zero=True))
    threshold: int = field(metadata=wire("thr", keep_zero=True))
    subsigs: list[MultisigSubsignature] = field(
        metadata=wire("subsig", encode=_encode_subsig_seq, decode=_decode_subsig_seq)
    )
