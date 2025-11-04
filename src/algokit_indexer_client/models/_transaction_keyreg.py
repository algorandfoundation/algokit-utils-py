# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class TransactionKeyreg:
    """
    Fields for a keyreg transaction.

    Definition:
    data/transactions/keyreg.go : KeyregTxnFields
    """

    non_participation: bool | None = field(
        default=None,
        metadata=wire("non-participation"),
    )
    selection_participation_key: bytes | None = field(
        default=None,
        metadata=wire("selection-participation-key"),
    )
    state_proof_key: bytes | None = field(
        default=None,
        metadata=wire("state-proof-key"),
    )
    vote_first_valid: int | None = field(
        default=None,
        metadata=wire("vote-first-valid"),
    )
    vote_key_dilution: int | None = field(
        default=None,
        metadata=wire("vote-key-dilution"),
    )
    vote_last_valid: int | None = field(
        default=None,
        metadata=wire("vote-last-valid"),
    )
    vote_participation_key: bytes | None = field(
        default=None,
        metadata=wire("vote-participation-key"),
    )
