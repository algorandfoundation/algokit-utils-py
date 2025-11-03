from dataclasses import dataclass, field

from algokit_transact.codec.serde import addr, nested, wire


@dataclass(slots=True, frozen=True)
class HeartbeatProof:
    signature: bytes | None = field(default=None, metadata=wire("s"))
    public_key: bytes | None = field(default=None, metadata=wire("p"))
    public_key_2: bytes | None = field(default=None, metadata=wire("p2"))
    public_key_1_signature: bytes | None = field(default=None, metadata=wire("p1s"))
    public_key_2_signature: bytes | None = field(default=None, metadata=wire("p2s"))


@dataclass(slots=True, frozen=True)
class HeartbeatTransactionFields:
    address: str | None = field(default=None, metadata=addr("a", omit_if_none=True))
    proof: HeartbeatProof | None = field(default=None, metadata=nested("prf", HeartbeatProof))
    seed: bytes | None = field(default=None, metadata=wire("sd"))
    vote_id: bytes | None = field(default=None, metadata=wire("vid"))
    key_dilution: int | None = field(default=None, metadata=wire("kd", keep_zero=True))
