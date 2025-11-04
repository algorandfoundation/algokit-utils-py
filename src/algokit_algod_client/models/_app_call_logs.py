# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class AppCallLogs:
    """
    The logged messages from an app call along with the app ID and outer transaction ID.
    Logs appear in the same order that they were emitted.
    """

    app_id: int = field(
        metadata=wire("app_id"),
    )
    logs: list[bytes] = field(
        metadata=wire("logs"),
    )
    tx_id: str = field(
        metadata=wire("txId"),
    )
