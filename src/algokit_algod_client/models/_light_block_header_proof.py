# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire

from ._serde_helpers import decode_bytes_base64, encode_bytes_base64


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
            encode=encode_bytes_base64,
            decode=decode_bytes_base64,
        ),
    )
    treedepth: int = field(
        default=0,
        metadata=wire("treedepth"),
    )
