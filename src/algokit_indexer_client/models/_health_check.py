# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class HealthCheck:
    """
    A health check response.
    """

    db_available: bool = field(
        metadata=wire("db-available"),
    )
    is_migrating: bool = field(
        metadata=wire("is-migrating"),
    )
    message: str = field(
        metadata=wire("message"),
    )
    round_: int = field(
        metadata=wire("round"),
    )
    version: str = field(
        metadata=wire("version"),
    )
    data: dict[str, object] | None = field(
        default=None,
        metadata=wire("data"),
    )
    errors: list[str] | None = field(
        default=None,
        metadata=wire("errors"),
    )
