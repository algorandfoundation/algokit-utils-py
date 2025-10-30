from __future__ import annotations

from dataclasses import dataclass, field

from algokit_transact.codec.serde import bytes_seq, nested, wire
from algokit_transact.signing.types import MultisigSignature


@dataclass(slots=True, frozen=True)
class LogicSignature:
    logic: bytes = field(metadata=wire("l"))
    args: tuple[bytes, ...] | None = field(default=None, metadata=bytes_seq("arg"))
    signature: bytes | None = field(default=None, metadata=wire("sig"))
    multi_signature: MultisigSignature | None = field(
        default=None,
        metadata=nested("msig", MultisigSignature),
    )
