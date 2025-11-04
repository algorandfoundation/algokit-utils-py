# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class ApplicationLogData:
    """
    Stores the global information associated with an application.
    """

    logs: list[bytes] = field(
        metadata=wire("logs"),
    )
    txid: str = field(
        metadata=wire("txid"),
    )
