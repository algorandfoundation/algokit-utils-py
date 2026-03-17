from pydantic import BaseModel, ConfigDict, Field


class SimulateRequestSchema(BaseModel):
    """Request type for simulation endpoint."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    txn_groups: "list[SimulateRequestTransactionGroupSchema]" = Field(alias="txn-groups")
    round_: int | None = Field(default=None, alias="round")
    allow_empty_signatures: bool | None = Field(default=None, alias="allow-empty-signatures")
    allow_more_logging: bool | None = Field(default=None, alias="allow-more-logging")
    allow_unnamed_resources: bool | None = Field(default=None, alias="allow-unnamed-resources")
    extra_opcode_budget: int | None = Field(default=None, alias="extra-opcode-budget")
    exec_trace_config: "SimulateTraceConfigSchema | None" = Field(default=None, alias="exec-trace-config")
    fix_signers: bool | None = Field(default=None, alias="fix-signers")
