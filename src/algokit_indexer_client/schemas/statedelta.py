from pydantic import RootModel


class StateDeltaSchema(RootModel[list["EvalDeltaKeyValueSchema"]]):
    """Application state delta."""
