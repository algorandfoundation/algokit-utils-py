# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire

from ._serde_helpers import decode_bytes_base64, encode_bytes_base64


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
            encode=encode_bytes_base64,
            decode=decode_bytes_base64,
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
            encode=encode_bytes_base64,
            decode=decode_bytes_base64,
        ),
    )
    state_proof_key: bytes | None = field(
        default=None,
        metadata=wire(
            "state-proof-key",
            encode=encode_bytes_base64,
            decode=decode_bytes_base64,
        ),
    )
