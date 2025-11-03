# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import nested, wire

from .state_proof_message import StateProofMessage


@dataclass(slots=True)
class StateProof:
    """
    Represents a state proof and its corresponding message
    """

    message: StateProofMessage = field(
        metadata=nested("Message", lambda: StateProofMessage),
    )
    state_proof: bytes = field(
        metadata=wire("StateProof"),
    )
