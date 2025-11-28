# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class CatchpointAbortResponse:
    """
    An catchpoint abort response.
    """

    catchup_message: str = field(
        default="",
        metadata=wire("catchup-message"),
    )
