from __future__ import annotations

from dataclasses import dataclass, field

from algokit_common.serde import nested, wire

from .state_proof_verifier import StateProofVerifier


@dataclass(slots=True)
class StateProofParticipant:
    verifier: StateProofVerifier | None = field(
        default=None,
        metadata=nested("verifier", lambda: StateProofVerifier),
    )
    weight: int | None = field(
        default=None,
        metadata=wire("weight"),
    )
