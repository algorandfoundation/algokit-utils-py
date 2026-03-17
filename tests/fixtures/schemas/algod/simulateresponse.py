from pydantic import BaseModel, ConfigDict, Field


class SimulateResponseSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    version: int = Field(alias="version")
    last_round: int = Field(alias="last-round")
    txn_groups: "list[SimulateTransactionGroupResultSchema]" = Field(alias="txn-groups")
    eval_overrides: "SimulationEvalOverridesSchema | None" = Field(default=None, alias="eval-overrides")
    exec_trace_config: "SimulateTraceConfigSchema | None" = Field(default=None, alias="exec-trace-config")
    initial_states: "SimulateInitialStatesSchema | None" = Field(default=None, alias="initial-states")
