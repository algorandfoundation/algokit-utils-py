from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class DryrunTxnResultSchema(BaseModel):
    """DryrunTxnResult contains any LogicSig or ApplicationCall program debug information and state updates from a dryrun."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    disassembly: list[str] = Field(default=None, alias="disassembly")
    logic_sig_disassembly: list[str] | None = Field(default=None, alias="logic-sig-disassembly")
    logic_sig_trace: "list[DryrunStateSchema] | None" = Field(default=None, alias="logic-sig-trace")
    logic_sig_messages: list[str] | None = Field(default=None, alias="logic-sig-messages")
    app_call_trace: "list[DryrunStateSchema] | None" = Field(default=None, alias="app-call-trace")
    app_call_messages: list[str] | None = Field(default=None, alias="app-call-messages")
    global_delta: "StateDeltaSchema | None" = Field(default=None, alias="global-delta")
    local_deltas: "list[AccountStateDeltaSchema] | None" = Field(default=None, alias="local-deltas")
    logs: list[str] | None = Field(default=None, alias="logs")
    budget_added: int | None = Field(default=None, alias="budget-added")
    budget_consumed: int | None = Field(default=None, alias="budget-consumed")
