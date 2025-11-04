# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class AccountParticipation:
    """
    AccountParticipation describes the parameters used by this account in consensus
    protocol.
    """

    selection_participation_key: bytes = field(
        metadata=wire("selection-participation-key"),
    )
    vote_first_valid: int = field(
        metadata=wire("vote-first-valid"),
    )
    vote_key_dilution: int = field(
        metadata=wire("vote-key-dilution"),
    )
    vote_last_valid: int = field(
        metadata=wire("vote-last-valid"),
    )
    vote_participation_key: bytes = field(
        metadata=wire("vote-participation-key"),
    )
    state_proof_key: bytes | None = field(
        default=None,
        metadata=wire("state-proof-key"),
    )
