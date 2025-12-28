# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire

from ._serde_helpers import decode_bytes, encode_bytes


@dataclass(slots=True)
class LightBlockHeaderProof:
    """
    Proof of membership and position of a light block header.
    """

    index: int = field(
        default=0,
        metadata=wire("index"),
    )
    proof: bytes = field(
        default=b"",
        metadata=wire(
            "proof",
            encode=encode_bytes,
            decode=decode_bytes,
        ),
    )
    treedepth: int = field(
        default=0,
        metadata=wire("treedepth"),
    )
