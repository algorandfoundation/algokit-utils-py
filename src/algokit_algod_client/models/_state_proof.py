# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import nested, wire

from ._serde_helpers import decode_bytes_base64, encode_bytes_base64
from ._state_proof_message import StateProofMessage


@dataclass(slots=True)
class StateProof:
    """
    Represents a state proof and its corresponding message
    """

    message: StateProofMessage = field(
        metadata=nested("Message", lambda: StateProofMessage),
    )
    state_proof: bytes = field(
        metadata=wire(
            "StateProof",
            encode=encode_bytes_base64,
            decode=decode_bytes_base64,
        ),
    )
