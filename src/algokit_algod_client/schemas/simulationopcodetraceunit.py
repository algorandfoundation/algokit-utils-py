from pydantic import BaseModel, ConfigDict, Field


class SimulationOpcodeTraceUnitSchema(BaseModel):
    """The set of trace information and effect from evaluating a single opcode."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    pc: int = Field(default=None, alias="pc")
    scratch_changes: "list[ScratchChangeSchema] | None" = Field(default=None, alias="scratch-changes")
    state_changes: "list[ApplicationStateOperationSchema] | None" = Field(default=None, alias="state-changes")
    spawned_inners: list[int] | None = Field(default=None, alias="spawned-inners")
    stack_pop_count: int | None = Field(default=None, alias="stack-pop-count")
    stack_additions: "list[AvmValueSchema] | None" = Field(default=None, alias="stack-additions")
