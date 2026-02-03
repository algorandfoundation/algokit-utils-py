from pydantic import BaseModel, ConfigDict, Field


class SimulateTransactionResultSchema(BaseModel):
    """Simulation result for an individual transaction"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    txn_result: "PendingTransactionResponseSchema" = Field(default=None, alias="txn-result")
    app_budget_consumed: int | None = Field(default=None, alias="app-budget-consumed")
    logic_sig_budget_consumed: int | None = Field(default=None, alias="logic-sig-budget-consumed")
    exec_trace: "SimulationTransactionExecTraceSchema | None" = Field(default=None, alias="exec-trace")
    unnamed_resources_accessed: "SimulateUnnamedResourcesAccessedSchema | None" = Field(
        default=None, alias="unnamed-resources-accessed"
    )
    fixed_signer: str | None = Field(default=None, alias="fixed-signer")
