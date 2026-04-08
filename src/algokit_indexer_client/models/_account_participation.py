# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire

from ._serde_helpers import decode_fixed_bytes, encode_fixed_bytes


@dataclass(slots=True)
class AccountParticipation:
    """
    AccountParticipation describes the parameters used by this account in consensus
    protocol.
    """

    selection_participation_key: bytes = field(
        default=b"",
        metadata=wire(
            "selection-participation-key",
            encode=lambda v: encode_fixed_bytes(v, 32),
            decode=lambda raw: decode_fixed_bytes(raw, 32),
        ),
    )
    vote_first_valid: int = field(
        default=0,
        metadata=wire("vote-first-valid"),
    )
    vote_key_dilution: int = field(
        default=0,
        metadata=wire("vote-key-dilution"),
    )
    vote_last_valid: int = field(
        default=0,
        metadata=wire("vote-last-valid"),
    )
    vote_participation_key: bytes = field(
        default=b"",
        metadata=wire(
            "vote-participation-key",
            encode=lambda v: encode_fixed_bytes(v, 32),
            decode=lambda raw: decode_fixed_bytes(raw, 32),
        ),
    )
    state_proof_key: bytes | None = field(
        default=None,
        metadata=wire(
            "state-proof-key",
            encode=lambda v: encode_fixed_bytes(v, 64),
            decode=lambda raw: decode_fixed_bytes(raw, 64),
        ),
    )
