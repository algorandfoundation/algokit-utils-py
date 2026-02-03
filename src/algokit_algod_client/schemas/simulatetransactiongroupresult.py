from pydantic import BaseModel, ConfigDict, Field


class SimulateTransactionGroupResultSchema(BaseModel):
    """Simulation result for an atomic transaction group"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    txn_results: "list[SimulateTransactionResultSchema]" = Field(default=None, alias="txn-results")
    failure_message: str | None = Field(default=None, alias="failure-message")
    failed_at: list[int] | None = Field(default=None, alias="failed-at")
    app_budget_added: int | None = Field(default=None, alias="app-budget-added")
    app_budget_consumed: int | None = Field(default=None, alias="app-budget-consumed")
    unnamed_resources_accessed: "SimulateUnnamedResourcesAccessedSchema | None" = Field(
        default=None, alias="unnamed-resources-accessed"
    )
