from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class SimulationTransactionExecTraceSchema(BaseModel):
    """The execution trace of calling an app or a logic sig, containing the inner app call trace in a recursive way."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    approval_program_trace: "list[SimulationOpcodeTraceUnitSchema] | None" = Field(
        default=None, alias="approval-program-trace"
    )
    approval_program_hash: str | None = Field(default=None, alias="approval-program-hash")
    clear_state_program_trace: "list[SimulationOpcodeTraceUnitSchema] | None" = Field(
        default=None, alias="clear-state-program-trace"
    )
    clear_state_program_hash: str | None = Field(default=None, alias="clear-state-program-hash")
    clear_state_rollback: bool | None = Field(default=None, alias="clear-state-rollback")
    clear_state_rollback_error: str | None = Field(default=None, alias="clear-state-rollback-error")
    logic_sig_trace: "list[SimulationOpcodeTraceUnitSchema] | None" = Field(default=None, alias="logic-sig-trace")
    logic_sig_hash: str | None = Field(default=None, alias="logic-sig-hash")
    inner_trace: "list[SimulationTransactionExecTraceSchema] | None" = Field(default=None, alias="inner-trace")
