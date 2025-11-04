# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class SimulationEvalOverrides:
    """
    The set of parameters and limits override during simulation. If this set of parameters
    is present, then evaluation parameters may differ from standard evaluation in certain
    ways.
    """

    allow_empty_signatures: bool | None = field(
        default=None,
        metadata=wire("allow-empty-signatures"),
    )
    allow_unnamed_resources: bool | None = field(
        default=None,
        metadata=wire("allow-unnamed-resources"),
    )
    extra_opcode_budget: int | None = field(
        default=None,
        metadata=wire("extra-opcode-budget"),
    )
    fix_signers: bool | None = field(
        default=None,
        metadata=wire("fix-signers"),
    )
    max_log_calls: int | None = field(
        default=None,
        metadata=wire("max-log-calls"),
    )
    max_log_size: int | None = field(
        default=None,
        metadata=wire("max-log-size"),
    )
