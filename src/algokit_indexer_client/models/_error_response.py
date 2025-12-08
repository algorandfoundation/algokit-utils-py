# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class ErrorResponse:
    message: str = field(
        default="",
        metadata=wire("message"),
    )
    data: dict[str, object] | None = field(
        default=None,
        metadata=wire("data"),
    )
