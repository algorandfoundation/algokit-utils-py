# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire

from ._serde_helpers import decode_bytes_sequence, encode_bytes_sequence


@dataclass(slots=True)
class ApplicationLogData:
    """
    Stores the global information associated with an application.
    """

    logs: list[bytes] = field(
        default_factory=list,
        metadata=wire(
            "logs",
            encode=encode_bytes_sequence,
            decode=decode_bytes_sequence,
        ),
    )
    tx_id: str = field(
        default="",
        metadata=wire("txid"),
    )
