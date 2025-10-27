from __future__ import annotations

from dataclasses import dataclass, field

from algokit_common.serde import wire

from ._serde_helpers import decode_model_sequence, encode_model_sequence
from .account_state_delta import AccountStateDelta
from .dryrun_state import DryrunState
from .eval_delta_key_value import EvalDeltaKeyValue


@dataclass(slots=True)
class DryrunTxnResult:
    """
    DryrunTxnResult contains any LogicSig or ApplicationCall program debug information and
    state updates from a dryrun.
    """

    disassembly: list[str] = field(
        metadata=wire("disassembly"),
    )
    app_call_messages: list[str] | None = field(
        default=None,
        metadata=wire("app-call-messages"),
    )
    app_call_trace: list[DryrunState] | None = field(
        default=None,
        metadata=wire(
            "app-call-trace",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: DryrunState, raw),
        ),
    )
    budget_added: int | None = field(
        default=None,
        metadata=wire("budget-added"),
    )
    budget_consumed: int | None = field(
        default=None,
        metadata=wire("budget-consumed"),
    )
    global_delta: list[EvalDeltaKeyValue] | None = field(
        default=None,
        metadata=wire(
            "global-delta",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: EvalDeltaKeyValue, raw),
        ),
    )
    local_deltas: list[AccountStateDelta] | None = field(
        default=None,
        metadata=wire(
            "local-deltas",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: AccountStateDelta, raw),
        ),
    )
    logic_sig_disassembly: list[str] | None = field(
        default=None,
        metadata=wire("logic-sig-disassembly"),
    )
    logic_sig_messages: list[str] | None = field(
        default=None,
        metadata=wire("logic-sig-messages"),
    )
    logic_sig_trace: list[DryrunState] | None = field(
        default=None,
        metadata=wire(
            "logic-sig-trace",
            encode=encode_model_sequence,
            decode=lambda raw: decode_model_sequence(lambda: DryrunState, raw),
        ),
    )
    logs: list[bytes] | None = field(
        default=None,
        metadata=wire("logs"),
    )
