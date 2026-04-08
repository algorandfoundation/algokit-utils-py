# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import nested, wire

from ._state_proof_signature import StateProofSignature


@dataclass(slots=True)
class StateProofSigSlot:
    lower_sig_weight: int | None = field(
        default=None,
        metadata=wire("lower-sig-weight"),
    )
    signature: StateProofSignature | None = field(
        default=None,
        metadata=nested("signature", lambda: StateProofSignature),
    )
