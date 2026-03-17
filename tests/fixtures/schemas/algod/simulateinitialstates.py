from pydantic import BaseModel, ConfigDict, Field


class SimulateInitialStatesSchema(BaseModel):
    """Initial states of resources that were accessed during simulation."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    app_initial_states: "list[ApplicationInitialStatesSchema] | None" = Field(default=None, alias="app-initial-states")
