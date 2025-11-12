# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire

from ._serde_helpers import decode_bytes_sequence, encode_bytes_sequence


@dataclass(slots=True)
class AppCallLogs:
    """
    The logged messages from an app call along with the app ID and outer transaction ID.
    Logs appear in the same order that they were emitted.
    """

    app_id: int = field(
        metadata=wire("application-index"),
    )
    logs: list[bytes] = field(
        metadata=wire(
            "logs",
            encode=encode_bytes_sequence,
            decode=decode_bytes_sequence,
        ),
    )
    tx_id: str = field(
        metadata=wire("txId"),
    )
