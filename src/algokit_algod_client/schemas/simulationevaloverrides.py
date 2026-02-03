from pydantic import BaseModel, ConfigDict, Field


class SimulationEvalOverridesSchema(BaseModel):
    """The set of parameters and limits override during simulation. If this set of parameters is present, then evaluation parameters may differ from standard evaluation in certain ways."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    allow_empty_signatures: bool | None = Field(default=None, alias="allow-empty-signatures")
    allow_unnamed_resources: bool | None = Field(default=None, alias="allow-unnamed-resources")
    max_log_calls: int | None = Field(default=None, alias="max-log-calls")
    max_log_size: int | None = Field(default=None, alias="max-log-size")
    extra_opcode_budget: int | None = Field(default=None, alias="extra-opcode-budget")
    fix_signers: bool | None = Field(default=None, alias="fix-signers")
