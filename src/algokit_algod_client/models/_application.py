# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import nested, wire

from ._application_params import ApplicationParams


@dataclass(slots=True)
class Application:
    """
    Application index and its parameters
    """

    params: ApplicationParams = field(
        metadata=nested("params", lambda: ApplicationParams, required=True),
    )
    id_: int = field(
        default=0,
        metadata=wire("id"),
    )
