# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire

from ._serde_helpers import decode_bytes_base64, encode_bytes_base64


@dataclass(slots=True)
class TransactionProof:
    """
    Proof of transaction in a block.
    """

    hashtype: str = field(
        metadata=wire("hashtype"),
    )
    idx: int = field(
        metadata=wire("idx"),
    )
    proof: bytes = field(
        metadata=wire(
            "proof",
            encode=encode_bytes_base64,
            decode=decode_bytes_base64,
        ),
    )
    stibhash: bytes = field(
        metadata=wire(
            "stibhash",
            encode=encode_bytes_base64,
            decode=decode_bytes_base64,
        ),
    )
    treedepth: int = field(
        metadata=wire("treedepth"),
    )
