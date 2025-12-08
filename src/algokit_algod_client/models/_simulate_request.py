# AUTO-GENERATED: oas_generator


from dataclasses import dataclass, field

from algokit_common.serde import nested, wire

from ._serde_helpers import decode_model_sequence, encode_model_sequence
from ._simulate_request_transaction_group import SimulateRequestTransactionGroup
from ._simulate_trace_config import SimulateTraceConfig


@dataclass(slots=True)
class SimulateRequest:
    """
    Request type for simulation endpoint.
    """

    txn_groups: list[SimulateRequestTransactionGroup] = field(
        default_factory=list,
        metadata=wire(
            "txn-groups",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: SimulateRequestTransactionGroup, raw),
        ),
    )
    allow_empty_signatures: bool | None = field(
        default=None,
        metadata=wire("allow-empty-signatures"),
    )
    allow_more_logging: bool | None = field(
        default=None,
        metadata=wire("allow-more-logging"),
    )
    allow_unnamed_resources: bool | None = field(
        default=None,
        metadata=wire("allow-unnamed-resources"),
    )
    exec_trace_config: SimulateTraceConfig | None = field(
        default=None,
        metadata=nested("exec-trace-config", lambda: SimulateTraceConfig),
    )
    extra_opcode_budget: int | None = field(
        default=None,
        metadata=wire("extra-opcode-budget"),
    )
    fix_signers: bool | None = field(
        default=None,
        metadata=wire("fix-signers"),
    )
    round_: int | None = field(
        default=None,
        metadata=wire("round"),
    )
