from __future__ import annotations

from dataclasses import dataclass, field

from algokit_common.serde import nested, wire

from .application_params import ApplicationParams


@dataclass(slots=True)
class Application:
    """
    Application index and its parameters
    """

    id_: int = field(
        metadata=wire("id"),
    )
    params: ApplicationParams = field(
        metadata=nested("params", lambda: ApplicationParams),
    )
