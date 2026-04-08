# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire

from ._serde_helpers import decode_bytes, encode_bytes


@dataclass(slots=True)
class TransactionProof:
    """
    Proof of transaction in a block.
    """

    hashtype: str = field(
        default="",
        metadata=wire("hashtype"),
    )
    idx: int = field(
        default=0,
        metadata=wire("idx"),
    )
    proof: bytes = field(
        default=b"",
        metadata=wire(
            "proof",
            encode=encode_bytes,
            decode=decode_bytes,
        ),
    )
    stibhash: bytes = field(
        default=b"",
        metadata=wire(
            "stibhash",
            encode=encode_bytes,
            decode=decode_bytes,
        ),
    )
    treedepth: int = field(
        default=0,
        metadata=wire("treedepth"),
    )
