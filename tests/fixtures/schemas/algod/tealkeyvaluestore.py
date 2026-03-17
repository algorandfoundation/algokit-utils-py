from pydantic import RootModel


class TealKeyValueStoreSchema(RootModel[list["TealKeyValueSchema"]]):
    """Represents a key-value store for use in an application."""

    pass
