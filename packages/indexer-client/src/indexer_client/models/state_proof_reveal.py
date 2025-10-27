from __future__ import annotations

from dataclasses import dataclass, field

from algokit_common.serde import nested, wire

from .state_proof_participant import StateProofParticipant
from .state_proof_sig_slot import StateProofSigSlot


@dataclass(slots=True)
class StateProofReveal:
    participant: StateProofParticipant | None = field(
        default=None,
        metadata=nested("participant", lambda: StateProofParticipant),
    )
    position: int | None = field(
        default=None,
        metadata=wire("position"),
    )
    sig_slot: StateProofSigSlot | None = field(
        default=None,
        metadata=nested("sig-slot", lambda: StateProofSigSlot),
    )
