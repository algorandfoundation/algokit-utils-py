# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class SimulateTraceConfig:
    """
    An object that configures simulation execution trace.
    """

    enable: bool | None = field(
        default=None,
        metadata=wire("enable"),
    )
    scratch_change: bool | None = field(
        default=None,
        metadata=wire("scratch-change"),
    )
    stack_change: bool | None = field(
        default=None,
        metadata=wire("stack-change"),
    )
    state_change: bool | None = field(
        default=None,
        metadata=wire("state-change"),
    )
