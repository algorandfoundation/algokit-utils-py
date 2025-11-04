# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class AlgodMutexAndBlockingProfilingState:
    """
    algod mutex and blocking profiling state.
    """

    block_rate: int | None = field(
        default=None,
        metadata=wire("block-rate"),
    )
    mutex_rate: int | None = field(
        default=None,
        metadata=wire("mutex-rate"),
    )
