# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import nested, wire

from ._serde_helpers import decode_bytes, encode_bytes
from ._state_proof_message import StateProofMessage


@dataclass(slots=True)
class StateProof:
    """
    Represents a state proof and its corresponding message
    """

    message: StateProofMessage = field(
        metadata=nested("Message", lambda: StateProofMessage, required=True),
    )
    state_proof: bytes = field(
        default=b"",
        metadata=wire(
            "StateProof",
            encode=encode_bytes,
            decode=decode_bytes,
        ),
    )
