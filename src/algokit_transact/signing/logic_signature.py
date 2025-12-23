from dataclasses import dataclass, field

from algokit_transact.codec.serde import bytes_seq, nested, wire
from algokit_transact.signing.types import MultisigSignature


@dataclass(slots=True, frozen=True)
class LogicSigSignature:
    logic: bytes = field(metadata=wire("l"))
    args: list[bytes] | None = field(default=None, metadata=bytes_seq("arg"))
    sig: bytes | None = field(default=None, metadata=wire("sig"))
    msig: MultisigSignature | None = field(
        default=None,
        metadata=nested("msig", MultisigSignature),
    )
    lmsig: MultisigSignature | None = field(
        default=None,
        metadata=nested("lmsig", MultisigSignature),
    )
