from typing import Any
from pydantic import RootModel


class ed25519PrivateKeySchema(RootModel[list[int]]):
    pass
