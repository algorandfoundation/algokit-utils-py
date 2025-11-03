from dataclasses import dataclass, field

from algokit_transact.codec.serde import wire


@dataclass(slots=True, frozen=True)
class KeyRegistrationTransactionFields:
    vote_key: bytes | None = field(default=None, metadata=wire("votekey"))
    selection_key: bytes | None = field(default=None, metadata=wire("selkey"))
    vote_first: int | None = field(default=None, metadata=wire("votefst"))
    vote_last: int | None = field(default=None, metadata=wire("votelst"))
    vote_key_dilution: int | None = field(default=None, metadata=wire("votekd"))
    state_proof_key: bytes | None = field(default=None, metadata=wire("sprfkey"))
    non_participation: bool | None = field(default=None, metadata=wire("nonpart"))
