# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class HealthCheck:
    """
    A health check response.
    """

    db_available: bool = field(
        default=False,
        metadata=wire("db-available"),
    )
    is_migrating: bool = field(
        default=False,
        metadata=wire("is-migrating"),
    )
    message: str = field(
        default="",
        metadata=wire("message"),
    )
    round_: int = field(
        default=0,
        metadata=wire("round"),
    )
    version: str = field(
        default="",
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
