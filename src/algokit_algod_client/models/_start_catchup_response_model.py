# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class StartCatchupResponseModel:
    """
    An catchpoint start response.
    """

    catchup_message: str = field(
        metadata=wire("catchup-message"),
    )
